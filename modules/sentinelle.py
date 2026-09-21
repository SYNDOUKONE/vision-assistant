import asyncio
import psutil
import subprocess
from modules import state
from modules.voice import parler
from modules.websocket_server import send_web_state

async def monitor_cyber_threats():
    """
    Boucle asynchrone qui tourne en fond pour le Mode Sentinelle Cyber.
    Surveille l'usage CPU/RAM, les appareils réseau (via ARP) et détecte
    quelques processus suspects de base.
    """
    known_macs = set()
    first_arp_run = True
    
    while True:
        if not state.MODE_SENTINELLE:
            await asyncio.sleep(5)
            continue
            
        try:
            # 1. Vérification CPU / RAM
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent
            
            if cpu_usage > 90:
                print(f"[SENTINELLE] Alerte CPU : {cpu_usage}%")
                await parler(f"Alerte sécurité Monsieur. Surcharge critique du processeur à {int(cpu_usage)} pourcent.")
                await send_web_state("error")
                await asyncio.sleep(10) # Pause anti-spam
                
            if ram_usage > 90:
                print(f"[SENTINELLE] Alerte RAM : {ram_usage}%")
                await parler(f"Alerte sécurité Monsieur. Utilisation de la mémoire vive critique, à {int(ram_usage)} pourcent.")
                await send_web_state("error")
                await asyncio.sleep(10)
                
            # 2. Vérification réseau (ARP pour détecter de nouveaux appareils)
            try:
                arp_output = subprocess.check_output(["arp", "-a"], text=True)
                current_macs = set()
                for line in arp_output.split('\n'):
                    if " at " in line:
                        parts = line.split(" at ")
                        if len(parts) > 1:
                            mac = parts[1].split(" ")[0]
                            # Filtrer l'adresse de broadcast
                            if mac != "ff:ff:ff:ff:ff:ff":
                                current_macs.add(mac)
                            
                if first_arp_run:
                    known_macs = current_macs
                    first_arp_run = False
                else:
                    new_macs = current_macs - known_macs
                    if new_macs:
                        print(f"[SENTINELLE] Nouvel appareil détecté : {new_macs}")
                        await parler("Alerte intrusion réseau Monsieur. Un nouvel appareil non identifié vient de se connecter au réseau local.")
                        await send_web_state("error")
                        known_macs.update(new_macs)
                        await asyncio.sleep(10)
            except Exception as e:
                print(f"[SENTINELLE] Erreur ARP : {e}")

            # 3. Heuristique (Processus suspects)
            for proc in psutil.process_iter(['name']):
                try:
                    p_name = proc.info.get('name')
                    if p_name:
                        name_low = p_name.lower()
                        if name_low in ["miner", "xmrig", "ncat"]:
                            print(f"[SENTINELLE] Processus suspect trouvé : {p_name}")
                            await parler(f"Menace potentielle détectée, Monsieur. Le processus suspect {p_name} est en cours d'exécution.")
                            await send_web_state("error")
                            await asyncio.sleep(15)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
                    
        except Exception as e:
            print(f"[SENTINELLE] Erreur générale: {e}")
            
        # Pause avant le prochain scan (15 secondes pour rester réactif sans trop consommer)
        await asyncio.sleep(15)

def start_sentinelle():
    asyncio.run(monitor_cyber_threats())
