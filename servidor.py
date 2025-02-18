import socket
import threading 
import time 
import ssl
from cryptography.fernet import Fernet
import json

class Cliente:
    def __init__(self, conexao, endereco):
        self.conexao = conexao  # Conexão TCP com o cliente
        self.endereco = endereco  # Endereço do cliente (IP e porta)
        self.userName = None
        self.ip = endereco[0]
        self.dados = {}

    def fecharConexao(self):
        try:
            self.conexao.close()
            print(f"Conexão com {self.userName} encerrada.")
        except Exception as e:
            print(f"Erro ao fechar conexão com {self.userName}: {e}")


class Servidor:
    def __init__(self, portBroadcast, portTCP):
        self.portBroadcast = portBroadcast
        self.portTCP = portTCP 
        self.hostTCP = '0.0.0.0'
        self.clientes = []
        self.running = True  # Controla se o servidor está em execução
        
        # Implementação do SSL
        self.certfile = 'server.crt'
        self.keyfile = 'server.key'

        # Para retirar
        self.key = Fernet.generate_key()  # Gera uma chave de criptografia
        self.cipher_suite = Fernet(self.key)  # Configura o objeto de criptografia com a chave gerada


    def iniciar(self):
        # Thread para enviar mensagens de broadcast
        threading.Thread(target=self.broadcastUDP).start()
        
        # Socket TCP
        self.socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  
        self.socket_tcp.bind((self.hostTCP, self.portTCP))
        self.socket_tcp.listen(15)
        
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.certfile, self.keyfile)
        
        # Escuta no máximo de 15 conexões
        print(f"Servidor TCP ouvindo na porta {self.portTCP}...")
       
        # Thread para ler comandos do terminal
        threading.Thread(target=self.lerComandos).start()
        
        # Loop principal para aceitar novas conexões TCP
        while self.running:
            conexao, endereco = self.socket_tcp.accept()
            cliente = Cliente(conexao, endereco)
            self.clientes.append(cliente)
            
            # Thread para lidar com o cliente
            threading.Thread(target=self.lidarCliente, args=(cliente,)).start()

    # Envia mensagens de broadcast
    def broadcastUDP(self):
        socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        socketUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        ip_servidor = socket.gethostbyname(socket.gethostname())  # Obtém o IP do servidor
        
        mensagem = f"SERVIDOR_TCP:{ip_servidor}:{self.portTCP}" 
        
        while self.running:  # Loop para enviar mensagens
            socketUDP.sendto(mensagem.encode(), ('<broadcast>', self.portBroadcast)) 
            #socketUDP.sendto(mensagem.encode(), ('10.25.255.255', self.portBroadcast)) # rede do ifrn
            time.sleep(30)

    # Lida com a comunicação com um cliente específico
    def lidarCliente(self, cliente):
        try:
            cliente.conexao.send(self.key)  # Envia a chave de criptografia ao cliente
           
            while self.running:
                dadosCriptografados = cliente.conexao.recv(1024)
                if not dadosCriptografados:  # Verifica se a conexão foi encerrada pelo cliente
                    print(f"Cliente {cliente.userName} desconectado.")
                    break 
                dados = self.descriptografar(dadosCriptografados)
                
                # Define o nome do usuário se ainda não foi definido
                if not cliente.userName:  
                    cliente.userName = dados.get("userName", "Desconhecido")
                    print(f"\nNovo cliente conectado: {cliente.userName} ({cliente.ip})")
                cliente.dados = dados
                print(f"Dados recebidos")
                
        except Exception as e:
            print(f"Erro ao lidar com cliente {cliente.userName}: {e}")

        finally:
            self.removerCliente(cliente)
    

    def descriptografar(self, dadosCriptografados):
        try:
            dadosDescriptografados = self.cipher_suite.decrypt(dadosCriptografados).decode()
            # Converte de volta para dicionário
            return json.loads(dadosDescriptografados) 
        
        except Exception as e:
            print(f"Erro ao descriptografar dados: {e}")
            return {}
        

    def removerCliente(self, cliente):
        if cliente in self.clientes:
            self.clientes.remove(cliente)
            cliente.fecharConexao()

    # Entrada de comandos no terminal
    def lerComandos(self):
        while self.running:
            comando = input("Digite um comando (help para lista):").strip().lower()
            
            if (comando == "help"): 
                print("Comandos disponíveis:")
                print("- listar: Mostra todos os clientes conectados.")
                print("- info [ip]: Mostra informações de um cliente específico.")
                print("- media: Mostra a média das informações numéricas de todos os clientes.")
                print("- desconectar [ip]: Desconecta um cliente específico.")
                print("- sair: Encerra o servidor.")

            elif (comando == "listar"): 
                for cliente in self.clientes:
                    print(f"{cliente.userName} ({cliente.ip})")

            elif (comando.startswith("info")):
               # Para fazer
               print("informaçoes do cliente")

            elif (comando == "media"):
                # Para fazer
                self.calcularMedia()
                
            elif (comando.startswith("desconectar")):
               # Para fazer
               print("desconectar cliente")

            elif (comando == "sair"): 
                self.running = False  # Altera o estado do servidor
                
                # Fecha a conexão com todos os clientes conectados
                for cliente in self.clientes:
                    cliente.fecharConexao()
                    self.clientes.remove(cliente)
               
                print("Encerrando servidor!")
                self.socket_tcp.close()
                
                break

    # indentificar cliente pelo IP
    def encontrarCliente(self, identificador):
        for cliente in self.clientes:  
            if (identificador == identificador == cliente.ip):  
                return cliente
        return None

    # Método para calcular a média das informações numéricas de todos os clientes
    def calcularMedia(self):
        if (not self.clientes):  # Verifica se há clientes conectados
            print("Nenhum cliente conectado.")
            return
        print("Médias de todos os dispositivos conectados:")

    # Método para criptografar dados
    def criptografar(self, dados):
        dadosJson = json.dumps(dados).encode()  # Converte os dados em JSON e codifica em bytes
        return self.cipher_suite.encrypt(dadosJson)

    

#=========================================================================================================================================

# Execução principal do programa
if __name__ == "__main__":
    servidor = Servidor(portBroadcast=5000, portTCP=6000)
    servidor.iniciar()