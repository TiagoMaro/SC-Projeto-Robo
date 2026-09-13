from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from excecoes import AtropelarHumanoError, ColisaoComParedeError, ColetarSemHumanoError, EjetarSemHumanoError, EjetarSemSaidaError
import csv

# Enum para representar as direções possíveis
class Direcao(Enum):
    CIMA = 0
    ESQUERDA = 1
    BAIXO = 2
    DIREITA = 3

# Mapeamento das direções para os deltas de linha e coluna
DELTAS_POR_DIRECAO = {
    Direcao.CIMA: (-1, 0),
    Direcao.BAIXO: (1, 0),
    Direcao.ESQUERDA: (0, -1),
    Direcao.DIREITA: (0, 1),
}

# Enum para representar os possíveis resultados da leitura dos sensores
class LeituraSensor(Enum):
    PAREDE = "PAREDE"
    VAZIO = "VAZIO"
    HUMANO = "HUMANO"
    SAIDA = "SAÍDA"
    
class SituacaoCarga(Enum):
    SEM_CARGA = "SEM CARGA"
    COM_HUMANO = "COM HUMANO"

# Função para calcular a próxima posição com base na posição atual e na direção
def calcular_proxima_posicao(posicao_atual: tuple, direcao: Direcao) -> tuple:
    delta_linha, delta_coluna = DELTAS_POR_DIRECAO[direcao]
    linha_atual, coluna_atual = posicao_atual
    return (linha_atual + delta_linha, coluna_atual + delta_coluna)

# Função para girar à esquerda a partir da direção atual
def girar_esquerda(direcao_atual: Direcao) -> Direcao:
    return Direcao((direcao_atual.value + 1) % 4)

@dataclass(frozen=True)
class ResultadoComando:
    """Resultado de um comando: as 3 leituras de sensor + situação da carga."""
    sensor_esquerdo: LeituraSensor
    sensor_frontal: LeituraSensor
    sensor_direito: LeituraSensor
    situacao_carga: SituacaoCarga

# PARTE PARA LER O LABIRINTO DO ARQUIVO
# Função para carregar o mapa do labirinto a partir de um arquivo
def carregar_mapa(caminho_arquivo: str) -> list:
    mapa = []
    with open(caminho_arquivo, 'r') as arquivo:
        for linha in arquivo:
            linha = linha.strip()
            if linha:  # Ignorar linhas vazias
                mapa.append(list(linha))
    return mapa

class Ambiente:
    def __init__(self, caminho_arquivo: str):
        self._mapa = carregar_mapa(caminho_arquivo)
        self.posicao_inicial = self._encontrar_posicao_inicial()
        self.direcao_inicial = Direcao.CIMA
        self.posicao_atual = self.posicao_inicial
        self.direcao_atual = self.direcao_inicial
        self.situacao_carga = SituacaoCarga.SEM_CARGA
        self.caminho_log = Path(caminho_arquivo).with_suffix('.csv')

    def _encontrar_posicao_inicial(self):
        for indice_linha, linha in enumerate(self._mapa):
            for indice_coluna, celula in enumerate(linha):
                if celula == '!':
                    return (indice_linha, indice_coluna)
        raise ValueError("Posição inicial não encontrada no mapa.")

    def ligar(self) -> ResultadoComando:
        """Liga o robô: não move nada, só lê os sensores na posição/direção iniciais."""
        leituras_atuais = self._ler_sensores()
        self._registrar_log("LIGAR", leituras_atuais)
        return leituras_atuais

    def executar_comando(self, comando: str) -> ResultadoComando:
        """Aplica um comando (A, G, P ou E) e devolve o resultado sensorial."""
        if comando == 'A':
            self._processar_avanco()
        elif comando == 'G':
            self.direcao_atual = girar_esquerda(self.direcao_atual)
        elif comando == 'P':
            self._processar_coleta()
        elif comando == 'E':
            self._processar_ejetar()
        leituras_atuais = self._ler_sensores()
        self._registrar_log(comando, leituras_atuais)
        return leituras_atuais

    def _processar_coleta(self):
        """Tenta pegar um humano na célula à frente do robô."""
        leitura_frontal = self._ler_direcao(self.direcao_atual)
        
        if leitura_frontal != LeituraSensor.HUMANO:
            raise ColetarSemHumanoError(
                "Comando 'P' bloqueado: não há humano na célula à frente."
            )
            
        # Calcula a posição exata para alterar o mapa
        posicao_alvo = calcular_proxima_posicao(self.posicao_atual, self.direcao_atual)
        linha_alvo, coluna_alvo = posicao_alvo
        
        # Atualiza o estado do robô e o mapa
        self.situacao_carga = SituacaoCarga.COM_HUMANO
        self._mapa[linha_alvo][coluna_alvo] = '.'

    def _processar_ejetar(self):
        leitura_frontal = self._ler_direcao(self.direcao_atual)
        if self.situacao_carga != SituacaoCarga.COM_HUMANO:
            raise EjetarSemHumanoError(
                "Comando 'E' bloqueado: não há humano na carga."
            )
        elif leitura_frontal != LeituraSensor.SAIDA:
            raise EjetarSemSaidaError(
                "Comando 'E' bloqueado: não está na saída."
            )
        else:
            self.situacao_carga = SituacaoCarga.SEM_CARGA

    def _processar_avanco(self):
        """Valida e, se estiver tudo certo, efetivamente move o robô uma célula."""
        posicao_destino = calcular_proxima_posicao(self.posicao_atual, self.direcao_atual)

        conteudo_destino = self._conteudo_da_celula(posicao_destino)

        if conteudo_destino == 'X':
            raise ColisaoComParedeError(
                f"Comando 'A' bloqueado: parede em {posicao_destino}"
            )
        if conteudo_destino == '@':
            raise AtropelarHumanoError(
                f"Comando 'A' bloqueado: humano em {posicao_destino}"
            )

        # Só chega aqui se passou nas duas validações -> agora sim move de verdade
        self.posicao_atual = posicao_destino

    def _ler_sensores(self) -> ResultadoComando:
        """Lê o que existe nas células à frente, esquerda e direita do robô."""
        leitura_frontal = self._ler_direcao(self.direcao_atual)
        leitura_esquerda = self._leitura_sensor_esquerda()
        leitura_direita = self._leitura_sensor_direita()

        return ResultadoComando(
            sensor_esquerdo=leitura_esquerda,
            sensor_frontal=leitura_frontal,
            sensor_direito=leitura_direita,
            situacao_carga=self.situacao_carga,
        )

    def _leitura_sensor_esquerda(self) -> LeituraSensor:
        """Lê o sensor esquerdo, sem alterar a direção real do robô."""
        direcao_calculada = girar_esquerda(self.direcao_atual)
        return self._ler_direcao(direcao_calculada)

    def _leitura_sensor_direita(self) -> LeituraSensor:
        """Lê o sensor direito, sem alterar a direção real do robô."""
        # Girar à esquerda 3 vezes equivale a girar 90° à direita uma vez
        direcao_calculada = girar_esquerda(girar_esquerda(girar_esquerda(self.direcao_atual)))
        return self._ler_direcao(direcao_calculada)
        
    def _conteudo_da_celula(self, posicao: tuple) -> str:
        """Retorna o caractere na célula (linha, coluna), tratando bordas fora do mapa."""
        linha, coluna = posicao
        total_linhas = len(self._mapa)
        
        # Validação contra índices negativos ou além dos limites
        if linha < 0 or linha >= total_linhas:
            return 'X'
        
        total_colunas = len(self._mapa[linha])
        if coluna < 0 or coluna >= total_colunas:
            return 'X'

        return self._mapa[linha][coluna]

    def _ler_direcao(self, direcao: Direcao) -> LeituraSensor:
        """Calcula a célula adjacente na direção informada e converte o caractere para LeituraSensor."""
        posicao_alvo = calcular_proxima_posicao(self.posicao_atual, direcao)
        caractere = self._conteudo_da_celula(posicao_alvo)

        # Mapeamento do caractere do mapa para a enumeração do sensor
        match caractere:
            case 'X':
                return LeituraSensor.PAREDE
            case '@':
                return LeituraSensor.HUMANO
            case 'S':  
                return LeituraSensor.SAIDA
            case '.': 
                return LeituraSensor.VAZIO
            case '!': 
                return LeituraSensor.VAZIO
            case _:
                raise ValueError(f"Caractere desconhecido no mapa: '{caractere}'")
            
    def _registrar_log(self, comando: str, resultado: ResultadoComando):
        """Registra o comando e o resultado sensorial em um arquivo CSV."""
        with open(self.caminho_log, mode='a', newline='', encoding='utf-8') as arquivo_csv:
            escritor_csv = csv.writer(arquivo_csv)
            escritor_csv.writerow([
                comando,
                resultado.sensor_esquerdo.value,
                resultado.sensor_direito.value,
                resultado.sensor_frontal.value,
                resultado.situacao_carga.value
            ])