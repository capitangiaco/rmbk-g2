import docker
import argparse
import os
import subprocess
import time

# Inizializza il client Docker
client = docker.from_env()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def start_vpn_services():
    print("Avvio dei servizi VPN (OpenVPN e WireGuard) con Docker...")

    # Avvio OpenVPN
    print("Avvio container OpenVPN...")
    try:
        client.containers.run(
            "kylemanna/openvpn",
            name="openvpn",
            cap_add=["NET_ADMIN"],
            ports={"1194/udp": 1194},
            volumes={f"{PROJECT_ROOT}/openvpn-data": {"bind": "/etc/openvpn", "mode": "rw"}},
            restart_policy={"Name": "unless-stopped"},
            detach=True
        )
        print("Container OpenVPN avviato.")
    except docker.errors.ContainerError as e:
        print(f"Errore durante l'avvio del container OpenVPN: {e}")
        print(f"Stdout: {e.stdout.decode()}")
        print(f"Stderr: {e.stderr.decode()}")
    except docker.errors.APIError as e:
        print(f"Errore API Docker durante l'avvio del container OpenVPN: {e}")
    
    # Avvio WireGuard
    print("Avvio container WireGuard...")
    try:
        client.containers.run(
            "linuxserver/wireguard",
            name="wireguard",
            cap_add=["NET_ADMIN"],
            environment={
                "PUID": "1000",
                "PGID": "1000",
                "TZ": "Europe/Rome",
                "SERVERURL": "192.168.2.11", # Assicurati che questo sia l'IP corretto
                "SERVERPORT": "51820",
                "PEERS": "1",
                "PEERDNS": "auto",
                "INTERNAL_SUBNET": "10.13.13.0/24"
            },
            volumes={
                f"{PROJECT_ROOT}/wireguard-data": {"bind": "/config", "mode": "rw"},
                "/lib/modules": {"bind": "/lib/modules", "mode": "ro"}
            },
            ports={"51820/udp": 51820},
            sysctls={
                "net.ipv4.ip_forward": "1"
            },
            restart_policy={"Name": "unless-stopped"},
            detach=True
        )
        print("Container WireGuard avviato.")
    except docker.errors.ContainerError as e:
        print(f"Errore durante l'avvio del container WireGuard: {e}")
        print(f"Stdout: {e.stdout.decode()}")
        print(f"Stderr: {e.stderr.decode()}")
    except docker.errors.APIError as e:
        print(f"Errore API Docker durante l'avvio del container WireGuard: {e}")

    print("Servizi VPN avviati.")

def stop_vpn_services():
    print("Arresto e rimozione dei servizi VPN (OpenVPN e WireGuard)...")

    # Arresto e rimozione OpenVPN
    try:
        openvpn_container = client.containers.get('openvpn')
        print("Arresto e rimozione container OpenVPN...")
        openvpn_container.stop()
        openvpn_container.remove()
        print("Container OpenVPN arrestato e rimosso.")
    except docker.errors.NotFound:
        print("Container OpenVPN non trovato o già arrestato/rimosso.")
    except docker.errors.APIError as e:
        print(f"Errore API Docker durante l'arresto/rimozione del container OpenVPN: {e}")

    # Arresto e rimozione WireGuard
    try:
        wireguard_container = client.containers.get('wireguard')
        print("Arresto e rimozione container WireGuard...")
        wireguard_container.stop()
        wireguard_container.remove()
        print("Container WireGuard arrestato e rimosso.")
    except docker.errors.NotFound:
        print("Container WireGuard non trovato o già arrestato/rimosso.")
    except docker.errors.APIError as e:
        print(f"Errore API Docker durante l'arresto/rimozione del container WireGuard: {e}")

    print("Servizi VPN arrestati e rimossi.")

def init_openvpn_pki():
    print("Inizializzazione della PKI di OpenVPN...")
    # Questo comando deve essere eseguito solo una volta per inizializzare la PKI
    # e generare il certificato CA e la chiave del server.

    # Genera il file di configurazione OVPN nel volume openvpn-data
    print("Generazione del file di configurazione OVPN...")
    try:
        client.containers.run(
            "kylemanna/openvpn",
            command="ovpn_genconfig -u udp://192.168.2.11",
            volumes={f"{PROJECT_ROOT}/openvpn-data": {"bind": "/etc/openvpn", "mode": "rw"}},
            environment={'OVPN_SERVER_URL': 'udp://192.168.2.11', 'EASYRSA_BATCH': '1'}, # Aggiungi OVPN_SERVER_URL e EASYRSA_BATCH
            remove=True, # Rimuove il container temporaneo dopo l'esecuzione
            detach=False # Esegui in foreground per catturare l'output
        )
        print("File di configurazione OVPN generato.")
    except docker.errors.ContainerError as e:
        print(f"Errore durante la generazione del file di configurazione OVPN: {e}")
        print(f"Stdout: {e.stdout.decode()}")
        print(f"Stderr: {e.stderr.decode()}")
        return
    except docker.errors.APIError as e:
        print(f"Errore API Docker durante la generazione del file di configurazione OVPN: {e}")
        return

    # Inizializza la PKI nel volume openvpn-data
    print("Inizializzazione della PKI...")
    try:
        result = client.containers.run(
            "kylemanna/openvpn",
            command="ovpn_initpki nopass",
            volumes={f"{PROJECT_ROOT}/openvpn-data": {"bind": "/etc/openvpn", "mode": "rw"}},
            environment={'OVPN_CN': '192.168.2.11', 'EASYRSA_BATCH': '1'}, # Passa il Common Name per la CA e EASYRSA_BATCH
            remove=True, # Rimuove il container temporaneo dopo l'esecuzione
            detach=False # Esegui in foreground per catturare l'output
        )
        print("PKI di OpenVPN inizializzata.")
        print(f"Output PKI: {result.decode()}")
    except docker.errors.ContainerError as e:
        print(f"Errore durante l'inizializzazione della PKI: {e.exit_status}")
        print(f"Stdout: {e.stdout.decode()}")
        print(f"Stderr: {e.stderr.decode()}")
        return
    except docker.errors.APIError as e:
        print(f"Errore API Docker durante l'inizializzazione della PKI: {e}")
        return

def create_openvpn_user(username):
    print(f"Creazione utente OpenVPN: {username}...")
    try:
        openvpn_container = client.containers.get('openvpn')
    except docker.errors.NotFound:
        print("Il container 'openvpn' non è in esecuzione. Avvialo prima.")
        return

    # Genera il certificato client
    openvpn_container.exec_run(f"easyrsa build-client-full {username} nopass", workdir="/etc/openvpn")
    # Esporta il file .ovpn
    result = openvpn_container.exec_run(f"ovpn_getclient {username}", workdir="/etc/openvpn")
    
    client_config_dir = os.path.join(PROJECT_ROOT, "client_configs", "openvpn")
    os.makedirs(client_config_dir, exist_ok=True)
    
    with open(os.path.join(client_config_dir, f"{username}.ovpn"), "w") as f:
        f.write(result.output.decode())
    print(f"Utente OpenVPN {username} creato. File di configurazione salvato in {client_config_dir}/{username}.ovpn")

def revoke_openvpn_user(username):
    print(f"Revoca utente OpenVPN: {username}...")
    try:
        openvpn_container = client.containers.get('openvpn')
    except docker.errors.NotFound:
        print("Il container 'openvpn' non è in esecuzione. Avvialo prima.")
        return
    
    openvpn_container.exec_run(f"easyrsa revoke {username}", workdir="/etc/openvpn")
    openvpn_container.exec_run("easyrsa gen-crl", workdir="/etc/openvpn")
    openvpn_container.exec_run("ovpn_copy_crl", workdir="/etc/openvpn")
    print(f"Utente OpenVPN {username} revocato.")

def list_openvpn_users():
    print("Elenco utenti OpenVPN (certificati validi):")
    try:
        openvpn_container = client.containers.get('openvpn')
    except docker.errors.NotFound:
        print("Il container 'openvpn' non è in esecuzione. Avvialo prima.")
        return
    
    result = openvpn_container.exec_run("easyrsa show-certs", workdir="/etc/openvpn")
    print(result.output.decode())

def create_wireguard_user(username):
    print(f"Creazione utente WireGuard: {username}...")
    try:
        wireguard_container = client.containers.get('wireguard')
    except docker.errors.NotFound:
        print("Il container 'wireguard' non è in esecuzione. Avvialo prima.")
        return

    # Genera chiavi per il client
    private_key_client = subprocess.run(["wg", "genkey"], capture_output=True, text=True, check=True).stdout.strip()
    public_key_client = subprocess.run(["wg", "pubkey"], input=private_key_client, capture_output=True, text=True, check=True).stdout.strip()

    # Ottieni la chiave pubblica del server WireGuard
    server_public_key_result = wireguard_container.exec_run("cat /config/wg_server_publickey")
    if server_public_key_result.exit_code != 0:
        print("Errore: Impossibile ottenere la chiave pubblica del server WireGuard. Assicurati che il server sia inizializzato.")
        return
    server_public_key = server_public_key_result.output.decode().strip()

    # Ottieni l'IP interno disponibile per il client
    # Questo è un placeholder. In un ambiente reale, dovresti gestire un pool di IP.
    # Per ora, useremo un IP fisso o un meccanismo semplice.
    # Per semplicità, assumiamo che il server sia 10.13.13.1 e i client partano da 10.13.13.2
    # Dovremmo leggere il file di configurazione del server per trovare l'ultimo IP assegnato
    # e assegnare il successivo.
    
    # Per ora, aggiungiamo semplicemente un peer al file di configurazione del server
    # e generiamo un IP casuale o sequenziale per il client.
    # Questo è un punto che richiede una logica più robusta per la gestione degli IP.
    
    # Leggi il file di configurazione del server WireGuard
    wg0_conf_result = wireguard_container.exec_run("cat /config/wg0.conf")
    if wg0_conf_result.exit_code != 0:
        print("Errore: Impossibile leggere il file di configurazione del server WireGuard.")
        return
    wg0_conf_content = wg0_conf_result.output.decode()

    # Trova l'ultimo IP assegnato e assegna il successivo
    # Questo è un esempio molto semplice e potrebbe non essere robusto per tutti gli scenari.
    # Una soluzione migliore sarebbe mantenere un registro degli IP assegnati.
    last_ip_octet = 1
    for line in wg0_conf_content.splitlines():
        if "AllowedIPs" in line and "10.13.13." in line:
            try:
                current_octet = int(line.split('.')[-1].split('/')[0])
                if current_octet > last_ip_octet:
                    last_ip_octet = current_octet
            except ValueError:
                pass
    client_ip = f"10.13.13.{last_ip_octet + 1}/32"

    # Aggiungi il peer al file di configurazione del server
    new_peer_config = f"""
[Peer]
PublicKey = {public_key_client}
AllowedIPs = {client_ip}
"""
    
    # Scrivi il nuovo contenuto nel file wg0.conf all'interno del container
    # Questo è un approccio diretto, ma in un ambiente di produzione si dovrebbe
    # considerare l'uso di `wg set` o la modifica del file e il riavvio del servizio.
    updated_wg0_conf = wg0_conf_content + new_peer_config
    wireguard_container.exec_run(f"sh -c 'echo \"{new_peer_config}\" >> /config/wg0.conf'")
    wireguard_container.exec_run("wg syncconf wg0 <(wg-quick strip wg0)") # Ricarica la configurazione

    # Genera il file di configurazione del client
    client_config = f"""
[Interface]
PrivateKey = {private_key_client}
Address = {client_ip}
DNS = 8.8.8.8

[Peer]
PublicKey = {server_public_key}
Endpoint = 192.168.2.11:51820 # Sostituisci con l'IP o il dominio del tuo server
AllowedIPs = 0.0.0.0/0, ::/0
PersistentKeepalive = 25
"""
    
    client_config_dir = os.path.join(PROJECT_ROOT, "client_configs", "wireguard")
    os.makedirs(client_config_dir, exist_ok=True)
    
    with open(os.path.join(client_config_dir, f"{username}.conf"), "w") as f:
        f.write(client_config)
    print(f"Utente WireGuard {username} creato. File di configurazione salvato in {client_config_dir}/{username}.conf")

def revoke_wireguard_user(username):
    print(f"Revoca utente WireGuard: {username}...")
    try:
        wireguard_container = client.containers.get('wireguard')
    except docker.errors.NotFound:
        print("Il container 'wireguard' non è in esecuzione. Avvialo prima.")
        return

    # Questo è più complesso per WireGuard, poiché non c'è un concetto di 'revoca' diretto come OpenVPN.
    # Dobbiamo rimuovere il peer dal file di configurazione wg0.conf.
    # Per farlo in modo robusto, dovremmo leggere il file, rimuovere il blocco [Peer] associato all'utente
    # e riscrivere il file, quindi ricaricare la configurazione.

    # Per ora, una soluzione semplificata: leggere il file, trovare la chiave pubblica dell'utente
    # (se l'abbiamo salvata da qualche parte) e rimuovere il blocco.
    # Questo richiede che tu abbia un modo per mappare il 'username' alla 'PublicKey' del client.
    # Per semplicità, assumiamo di dover rimuovere un peer dato il suo IP o la sua chiave pubblica.
    # Per questo esempio, non implementeremo la revoca completa senza un meccanismo di mappatura utente-chiave.
    print("La revoca di utenti WireGuard richiede un meccanismo per identificare il peer (es. tramite chiave pubblica o IP).")
    print("Questa funzione non è ancora completamente implementata senza un database di utenti.")

def list_wireguard_users():
    print("Elenco utenti WireGuard:")
    try:
        wireguard_container = client.containers.get('wireguard')
    except docker.errors.NotFound:
        print("Il container 'wireguard' non è in esecuzione. Avvialo prima.")
        return
    
    result = wireguard_container.exec_run("wg show wg0")
    print(result.output.decode())

def main():
    parser = argparse.ArgumentParser(description="Gestore di utenti VPN (OpenVPN e WireGuard) su Docker.")
    subparsers = parser.add_subparsers(dest="command", help="Comando da eseguire")

    # Comandi per Docker Compose
    parser_start = subparsers.add_parser("start", help="Avvia i servizi VPN con Docker Compose.")
    parser_stop = subparsers.add_parser("stop", help="Arresta i servizi VPN con Docker Compose.")

    # Comandi per OpenVPN
    parser_openvpn = subparsers.add_parser("openvpn", help="Gestione utenti OpenVPN.")
    openvpn_subparsers = parser_openvpn.add_subparsers(dest="openvpn_command", help="Comando OpenVPN")

    openvpn_init = openvpn_subparsers.add_parser("init-pki", help="Inizializza la PKI di OpenVPN (da eseguire una sola volta).")

    openvpn_create = openvpn_subparsers.add_parser("create", help="Crea un nuovo utente OpenVPN.")
    openvpn_create.add_argument("username", type=str, help="Nome utente per OpenVPN.")

    openvpn_revoke = openvpn_subparsers.add_parser("revoke", help="Revoca un utente OpenVPN.")
    openvpn_revoke.add_argument("username", type=str, help="Nome utente da revocare per OpenVPN.")

    openvpn_list = openvpn_subparsers.add_parser("list", help="Elenca gli utenti OpenVPN.")

    # Comandi per WireGuard
    parser_wireguard = subparsers.add_parser("wireguard", help="Gestione utenti WireGuard.")
    wireguard_subparsers = parser_wireguard.add_subparsers(dest="wireguard_command", help="Comando WireGuard")

    wireguard_create = wireguard_subparsers.add_parser("create", help="Crea un nuovo utente WireGuard.")
    wireguard_create.add_argument("username", type=str, help="Nome utente per WireGuard.")

    wireguard_revoke = wireguard_subparsers.add_parser("revoke", help="Revoca un utente WireGuard.")
    wireguard_revoke.add_argument("username", type=str, help="Nome utente da revocare per WireGuard.")

    wireguard_list = wireguard_subparsers.add_parser("list", help="Elenca gli utenti WireGuard.")

    args = parser.parse_args()

    if args.command == "start":
        start_vpn_services()
    elif args.command == "stop":
        stop_vpn_services()
    elif args.command == "openvpn":
        if args.openvpn_command == "init-pki":
            init_openvpn_pki()
        elif args.openvpn_command == "create":
            create_openvpn_user(args.username)
        elif args.openvpn_command == "revoke":
            revoke_openvpn_user(args.username)
        elif args.openvpn_command == "list":
            list_openvpn_users()
    elif args.command == "wireguard":
        if args.wireguard_command == "create":
            create_wireguard_user(args.username)
        elif args.wireguard_command == "revoke":
            revoke_wireguard_user(args.username)
        elif args.wireguard_command == "list":
            list_wireguard_users()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
