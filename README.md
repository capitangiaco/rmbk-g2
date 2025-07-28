# RMBK-G2 VPN Concentrator

This project manages an OpenVPN and WireGuard VPN concentrator using Docker Compose and a Python script.

## Initial Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your_user/RMBK-G2.git
    cd RMBK-G2
    ```

2.  **Update the server IP:**
    In `docker-compose.yml` and `vpn_manager.py`, the server IP address is currently set to `192.168.2.11` (for development purposes).
    **Remember to replace this value with your public server IP or domain** before going into production.

3.  **Install Python dependencies:**
    ```bash
    pip install docker
    ```

## Usage

### Start VPN Services
```bash
python3 vpn_manager.py start
```

### Stop VPN Services
```bash
python3 vpn_manager.py stop
```

### OpenVPN Management

#### Initialize PKI (first time only)
```bash
python3 vpn_manager.py openvpn init-pki
```

#### Create an OpenVPN User
```bash
python3 vpn_manager.py openvpn create <username>
```
The `.ovpn` client file will be saved in the `client_configs/openvpn/` directory.

#### Revoke an OpenVPN User
```bash
python3 vpn_manager.py openvpn revoke <username>
```

#### List OpenVPN Users
```bash
python3 vpn_manager.py openvpn list
```

### WireGuard Management

#### Create a WireGuard User
```bash
python3 vpn_manager.py wireguard create <username>
```
The `.conf` client file will be saved in the `client_configs/wireguard/` directory.

#### Revoke a WireGuard User (limited functionality)
Currently, revoking WireGuard users requires manual removal of the peer from the server configuration file or the implementation of a more robust user-to-key mapping mechanism.

#### List WireGuard Users
```bash
python3 vpn_manager.py wireguard list
```

## Connection Monitoring

### OpenVPN

To view active OpenVPN connections, you can access the container shell and read the status file:

1.  **Access the OpenVPN container shell:**
    ```bash
    docker exec -it openvpn bash
    ```
2.  **View status:**
    Inside the container, the status file is usually located at `/etc/openvpn/openvpn-status.log`.
    ```bash
    cat /etc/openvpn/openvpn-status.log
    ```
    (Exit the container shell with `exit`)

### WireGuard

To view the status of active WireGuard connections, use the script's `list` command:

```bash
python3 vpn_manager.py wireguard list
```
This command executes `wg show wg0` inside the WireGuard container and will show you connected peers and their last handshake.

---

**Note:** Currently, the development of this project is paused because Guly trolled me. 😜

---

# RMBK-G2 Concentratore VPN

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
python3 vpn_manager.py start
```

### Arrestare i servizi VPN
```bash
python3 vpn_manager.py stop
```

### Gestione OpenVPN

#### Inizializzare la PKI (solo la prima volta)
```bash
python3 vpn_manager.py openvpn init-pki
```

#### Creare un utente OpenVPN
```bash
python3 vpn_manager.py openvpn create <nome_utente>
```
Il file `.ovpn` per il client verrà salvato nella directory `client_configs/openvpn/`.

#### Revocare un utente OpenVPN
```bash
python3 vpn_manager.py openvpn revoke <nome_utente>
```

#### Elencare gli utenti OpenVPN
```bash
python3 vpn_manager.py openvpn list
```

### Gestione WireGuard

#### Creare un utente WireGuard
```bash
python3 vpn_manager.py wireguard create <nome_utente>
```
Il file `.conf` verrà salvato nella directory `client_configs/wireguard/`.

#### Revocare un utente WireGuard (funzionalità limitata)
Attualmente, la revoca di utenti WireGuard richiede la rimozione manuale del peer dal file di configurazione del server o l'implementazione di un meccanismo di mappatura utente-chiave più robusto.

#### Elencare gli utenti WireGuard
```bash
python3 vpn_manager.py wireguard list
```

## Monitoraggio delle Connessioni

### OpenVPN

Per visualizzare le connessioni attive di OpenVPN, puoi accedere alla shell del container e leggere il file di stato:

1.  **Accedi alla shell del container OpenVPN:**
    ```bash
    docker exec -it openvpn bash
    ```
2.  **Visualizza lo stato:**
    All'interno del container, il file di stato si trova solitamente in `/etc/openvpn/openvpn-status.log`.
    ```bash
    cat /etc/openvpn/openvpn-status.log
    ```
    (Esci dalla shell del container con `exit`)

### WireGuard

Per visualizzare lo stato delle connessioni attive di WireGuard, usa il comando `list` dello script:

```bash
python3 vpn_manager.py wireguard list
```
Questo comando esegue `wg show wg0` all'interno del container WireGuard e ti mostrerà i peer connessi e il loro ultimo handshake.

---

**Nota:** Al momento, lo sviluppo di questo progetto è in pausa perché il Guly mi ha trollato. 😜