import docker
import argparse
import os
import subprocess

# Inizializza il client Docker
client = docker.from_env()

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

def run_docker_compose_command(command_args, description):
    cmd = ["docker-compose"] + command_args
    print(f"Esecuzione comando: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, check=True)
        print(f"Stdout:\n{result.stdout}")
        if result.stderr:
            print(f"Stderr:\n{result.stderr}")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Errore durante l'esecuzione del comando Docker Compose: {e}")
        print(f"Stdout:\n{e.stdout}")
        print(f"Stderr:\n{e.stderr}")
        raise

def start_vpn_services():
    print("Avvio dei servizi VPN (OpenVPN e WireGuard) con Docker Compose...")
    run_docker_compose_command(["up", "-d"], "Avvio dei servizi VPN")
    print("Servizi VPN avviati.")

def stop_vpn_services():
    print("Arresto dei servizi VPN (OpenVPN e WireGuard) con Docker Compose...")
    run_docker_compose_command(["down"], "Arresto dei servizi VPN")
    print("Servizi VPN arrestati.")

def init_openvpn_pki():
    print("Inizializzazione della PKI di OpenVPN...")
    # Questo comando deve essere eseguito solo una volta per inizializzare la PKI
    # e generare il certificato CA e la chiave del server.
    # Assicurati che il container OpenVPN sia in esecuzione.
    try:
        openvpn_container = client.containers.get('openvpn')
    except docker.errors.NotFound:
        print("Il container 'openvpn' non è in esecuzione. Avvialo prima.")
        return

    # Inizializza la PKI
    print("Generazione del file di configurazione OVPN...")
    openvpn_container.exec_run("ovpn_genconfig -u udp://192.168.2.11", workdir="/etc/openvpn")
    print("Inizializzazione della PKI...")
    openvpn_container.exec_run("ovpn_initpki", workdir="/etc/openvpn")
    print("PKI di OpenVPN inizializzata.")

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
        f.write(result.stdout.decode())
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
    print(result.stdout.decode())

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
    server_public_key_result = wireguard_container.exec_run("cat /config/wg_server_publickey", text=True)
    if server_public_key_result.exit_code != 0:
        print("Errore: Impossibile ottenere la chiave pubblica del server WireGuard. Assicurati che il server sia inizializzato.")
        return
    server_public_key = server_public_key_result.stdout.strip()

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
    wg0_conf_result = wireguard_container.exec_run("cat /config/wg0.conf", text=True)
    if wg0_conf_result.exit_code != 0:
        print("Errore: Impossibile leggere il file di configurazione del server WireGuard.")
        return
    wg0_conf_content = wg0_conf_result.stdout

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
    wireguard_container.exec_run(f"sh -c 'echo \"{new_peer_config}\" >> /config/wg0.conf'", text=True)
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
    
    result = wireguard_container.exec_run("wg show wg0", text=True)
    print(result.stdout)

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
