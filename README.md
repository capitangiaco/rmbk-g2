# RMBK-G2 VPN Concentrator

Questo progetto gestisce un concentratore VPN con OpenVPN e WireGuard tramite Docker Compose e uno script Python.

## Configurazione Iniziale

1.  **Clona il repository:**
    ```bash
    git clone https://github.com/tuo_utente/RMBK-G2.git
    cd RMBK-G2
    ```

2.  **Aggiorna l'IP del server:**
    Nel file `docker-compose.yml` e `vpn_manager.py`, l'indirizzo IP del server è attualmente impostato su `192.168.2.11` (per scopi di sviluppo).
    **Ricorda di sostituire questo valore con l'IP pubblico o il dominio del tuo server di produzione** prima di andare in produzione.

3.  **Installa le dipendenze Python:**
    ```bash
    pip install docker
    ```

## Utilizzo

### Avviare i servizi VPN
```bash
python vpn_manager.py start
```

### Arrestare i servizi VPN
```bash
python vpn_manager.py stop
```

### Gestione OpenVPN

#### Inizializzare la PKI (solo la prima volta)
```bash
python vpn_manager.py openvpn init-pki
```

#### Creare un utente OpenVPN
```bash
python vpn_manager.py openvpn create <nome_utente>
```
Il file `.ovpn` verrà salvato nella directory `client_configs/openvpn/`.

#### Revocare un utente OpenVPN
```bash
python vpn_manager.py openvpn revoke <nome_utente>
```

#### Elencare gli utenti OpenVPN
```bash
python vpn_manager.py openvpn list
```

### Gestione WireGuard

#### Creare un utente WireGuard
```bash
python vpn_manager.py wireguard create <nome_utente>
```
Il file `.conf` verrà salvato nella directory `client_configs/wireguard/`.

#### Revocare un utente WireGuard (funzionalità limitata)
Attualmente, la revoca di utenti WireGuard richiede la rimozione manuale del peer dal file di configurazione del server o l'implementazione di un meccanismo di mappatura utente-chiave più robusto.

#### Elencare gli utenti WireGuard
```bash
python vpn_manager.py wireguard list
```
