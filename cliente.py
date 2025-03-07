import socket
import threading 
import time 
import psutil
import os
from cryptography.fernet import Fernet
import json

# Função para coletar informações do sistema
def coletar_informacoes():
    try:
        # Cria um dicionário para armazenar as informações coletadas
        info = {
            "nome_usuario": os.getlogin(),
            "ipv4": socket.gethostbyname(socket.gethostname()),
            "cores": psutil.cpu_count(logical=True),
            "ram_total": round(psutil.virtual_memory().total / (1024 ** 3), 2), 
            "ram_livre": round(psutil.virtual_memory().available / (1024 ** 3), 2),
            "disco_total": round(psutil.disk_usage('/').total / (1024 ** 3), 2),
            "disco_livre": round(psutil.disk_usage('/').free / (1024 ** 3), 2),
        }

        return info 
    
    except Exception as e:
        print(f"Erro ao coletar informações: {e}")
        return {}


class Cliente:
    def __init__(self, broadcast_port=5000): 
        self.broadcastPort = broadcast_port 
        self.servidorEndereco = None
        self.key = None 
        self.cipherSuite = None

    # Método para iniciar o cliente
    def iniciar(self):
        # Thread para escutar mensagens de broadcast UDP
        threading.Thread(target=self.escutarBroadcast).start()

    # Método para escutar mensagens de broadcast UDP
    def escutarBroadcast(self):
        socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socketUDP.bind(('0.0.0.0', self.broadcastPort))
        print("Escutando broadcast...") 

        while True:
            mensagem, _ = socketUDP.recvfrom(1024)  # Recebe a mensagem pelo UDP com tamanho máximo de 1024 bytes
            mensagem = mensagem.decode()
            
            if mensagem.startswith("SERVIDOR_TCP:"):  # Verifica se a mensagem começa com "SERVIDOR_TCP:"
                _, ip_servidor, porta = mensagem.split(":")
                self.servidorEndereco = (ip_servidor, int(porta))
                print(f"Servidor encontrado: {self.servidorEndereco}")
                break
        
        # Fechando socket UDP do cliente
        socketUDP.close()  
        
        # Conectando ao servidor via TCP
        self.conectarServidorTCP()  

    # Método para conectar-se ao servidor via TCP
    def conectarServidorTCP(self):
        socketTCP = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socketTCP.connect(self.servidorEndereco)
        
        self.key = socketTCP.recv(1024)  # Recebe a chave de criptografia enviada pelo servidor
        self.cipherSuite = Fernet(self.key)  # Configura o objeto de criptografia com a chave recebida
        print("Conectado ao servidor.")
        
        # Thread para enviar informações ao servidor
        threading.Thread(target=self.enviarInformacoes, args=(socketTCP,)).start()

    # Envia informações via TCP
    def enviarInformacoes(self, tcp_socket):
        while True:
            informacoes = coletar_informacoes() 
            dadosCriptografados = self.criptografar(informacoes)
            try:    
                tcp_socket.send(dadosCriptografados)
                print("Dados enviados")
            
            except (BrokenPipeError, ConnectionResetError):
                print("Erro: conexão perdida com o servidor.")
                return
            time.sleep(30)

    # Método para criptografar dados
    def criptografar(self, dados):
        dadosJson = json.dumps(dados).encode() 
        return self.cipherSuite.encrypt(dadosJson)  # Converte os dados em string, codifica em bytes e criptografa

# Execução principal do programa
if __name__ == "__main__":
    cliente = Cliente()
    cliente.iniciar()