import socket
import threading 
import time 
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
    def __init__(self, portBroadcast=5000, portTCP=6000):
        self.portBroadcast = portBroadcast  # Porta de broadcast UDP
        self.portTCP = portTCP  # Porta para conexões TCP
        self.clientes = []  # Lista de clientes conectados
        self.running = True  # Controla se o servidor está em execução
        self.key = Fernet.generate_key()  # Gera uma chave de criptografia
        self.cipher_suite = Fernet(self.key)  # Configura o objeto de criptografia com a chave gerada

    # Método para iniciar o servidor
    def iniciar(self):
        # Inicia uma thread para enviar mensagens de broadcast UDP
        threading.Thread(target=self.broadcastUDP).start()
        
        # Cria um socket TCP para aceitar conexões
        self.socket_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # Cria um socket TCP
        self.socket_tcp.bind(('', self.portTCP))  # socket na porta TCP 
        self.socket_tcp.listen(15)  # Socket escutando no máximo de 15 conexões
        print(f"Servidor TCP ouvindo na porta {self.portTCP}...")
       
        # Inicia uma thread para ler comandos do terminal
        threading.Thread(target=self.lerComandos).start()
        
        # Loop principal para aceitar novas conexões TCP
        while self.running:
            conexao, endereco = self.socket_tcp.accept()  # Aceita uma nova conexão TCP
            cliente = Cliente(conexao, endereco)  # Cria um objeto Cliente para representar o cliente conectado
            self.clientes.append(cliente)  # Adiciona o cliente à lista de clientes
            
            # Inicia uma thread para lidar com o cliente
            threading.Thread(target=self.lidarCliente, args=(cliente,)).start()

    # Método para enviar mensagens de broadcast UDP
    def broadcastUDP(self):
        socketUDP = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Cria um socket UDP
        
        socketUDP.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)  # envio de broadcast
        ip_servidor = socket.gethostbyname(socket.gethostname())  # Obtém o IP do servidor
        
        mensagem = f"SERVIDOR_TCP:{ip_servidor}:{self.portTCP}"  # Cria a mensagem de broadcast com IP e porta TCP
        
        while self.running:  # Loop infinito para enviar mensagens de broadcast
            socketUDP.sendto(mensagem.encode(), ('10.25.255.255', self.portBroadcast)) # Envia a mensagem na rede
            time.sleep(30)

    # Lida com a comunicação com um cliente específico
    def lidarCliente(self, cliente):
        try:
            cliente.conexao.send(self.key)  # Envia a chave de criptografia ao cliente
           
            while self.running:  # Loop infinito para receber dados do cliente
                dadosCriptografados = cliente.conexao.recv(1024)  # Recebe dados criptografados do cliente (tamanho máximo de 1024 bytes)
                if not dadosCriptografados:  # Verifica se a conexão foi encerrada pelo cliente
                    print(f"Cliente {cliente.userName} desconectado.")
                    break 
                dados = self.descriptografar(dadosCriptografados)  # Descriptografa os dados recebidos
                
                if not cliente.userName:  # Define o nome do usuário se ainda não foi definido
                    cliente.userName = dados.get("userName", "Desconhecido")
                    print(f"\nNovo cliente conectado: {cliente.userName} ({cliente.ip})")
                cliente.dados = dados  # Atualiza os dados do cliente
                print(f"Dados recebidos")
                
        except Exception as e:
            print(f"Erro ao lidar com cliente {cliente.userName}: {e}")

        finally:
            self.removerCliente(cliente)  # Remove o cliente da lista de clientes conectados

    # Método para remover um cliente da lista de clientes conectados
    def removerCliente(self, cliente):
        if cliente in self.clientes:  # Verifica se o cliente está na lista
            self.clientes.remove(cliente)  # Remove o cliente da lista
            cliente.fecharConexao()  # Fecha a conexão com o cliente

    # Método para ler comandos digitados no terminal
    def lerComandos(self):
        while self.running:  # Loop infinito para ler comandos
            comando = input("Digite um comando (help para lista):").strip().lower()  # Lê o comando do terminal
            if comando == "help":  # Exibe a lista de comandos disponíveis
                print("Comandos disponíveis:")
                print("- listar: Mostra todos os clientes conectados.")
                print("- info [ip]: Mostra informações de um cliente específico.")
                print("- media: Mostra a média das informações numéricas de todos os clientes.")
                print("- desconectar [ip]: Desconecta um cliente específico.")
                print("- sair: Encerra o servidor.")

            elif comando == "listar": 
                for cliente in self.clientes:
                    print(f"{cliente.userName} ({cliente.ip})")

            elif comando.startswith("info"):
               # Para fazer
               print("informaçoes do cliente")

            elif comando == "media":
                # Para fazer
                self.calcularMedia()
                
            elif comando.startswith("desconectar"):
               # Para fazer
               print("desconectar cliente")

            elif comando == "sair":  # Encerra o servidor
                self.running = False  # Altera o estado do servidor
                
                # Fecha a conexão com todos os clientes conectados
                for cliente in self.clientes:
                    cliente.fecharConexao()
                print("Encerrando servidor!")
                break

    # Método para encontrar um cliente pelo nome ou IP
    def encontrarCliente(self, identificador):
        for cliente in self.clientes:  # Itera sobre a lista de clientes
            if identificador == cliente.userName or identificador == cliente.ip:  # Verifica se o identificador corresponde ao nome ou IP
                return cliente
        return None

    # Método para calcular a média das informações numéricas de todos os clientes
    def calcularMedia(self):
        if not self.clientes:  # Verifica se há clientes conectados
            print("Nenhum cliente conectado.")
            return
        print("Médias de todos os dispositivos conectados:")

    # Método para criptografar dados
    def criptografar(self, dados):
        dadosJson = json.dumps(dados).encode()  # Converte os dados em JSON e codifica em bytes
        return self.cipher_suite.encrypt(dadosJson)

    # Método para descriptografar dados
    def descriptografar(self, dadosCriptografados):
        try:
            dadosDescriptografados = self.cipher_suite.decrypt(dadosCriptografados).decode()  # Descriptografa e decodifica
            return json.loads(dadosDescriptografados)  # Converte de volta para dicionário
        
        except Exception as e:
            print(f"Erro ao descriptografar dados: {e}")
            return {}

#=========================================================================================================================================

# Execução principal do programa
if __name__ == "__main__":
    servidor = Servidor()
    servidor.iniciar()