from enum import Enum

# PARTE DE DIREÇÃO DO ROBOT
# Enum para representar as direções possíveis
class Direcao(Enum):
    CIMA = 0
    ESQUERDA = 1
    # BAIXO = 2
    DIREITA = 3

# Mapeamento das direções para os deltas de linha e coluna
DELTAS_POR_DIRECAO = {
    Direcao.CIMA: (-1, 0),
    Direcao.BAIXO: (1, 0),
    Direcao.ESQUERDA: (0, -1),
    Direcao.DIREITA: (0, 1),
}

# Função para calcular a próxima posição com base na posição atual e na direção
def calcular_proxima_posicao(posicao_atual: tuple, direcao: Direcao) -> tuple:
    delta_linha, delta_coluna = DELTAS_POR_DIRECAO[direcao]
    linha_atual, coluna_atual = posicao_atual
    return (linha_atual + delta_linha, coluna_atual + delta_coluna)

# Função para girar à esquerda a partir da direção atual
def girar_esquerda(direcao_atual: Direcao) -> Direcao:
    return Direcao((direcao_atual.value + 1) % 4)


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

    def _encontrar_posicao_inicial(self):
        for indice_linha, linha in enumerate(self._mapa):
            for indice_coluna, celula in enumerate(linha):
                if celula == '!':
                    return (indice_linha, indice_coluna)
        raise ValueError("Posição inicial não encontrada no mapa.")

    class LeituraSensor(Enum):
        PAREDE = "PAREDE"
        VAZIO = "VAZIO"
        HUMANO = "HUMANO"
        SAIDA = "SAÍDA"


class AlarmeRobo(Exception):
    """Classe base para todos os alarmes de segurança do robô."""
    pass

class ColisaoComParedeError(AlarmeRobo):
    """Exceção levantada quando o robô colide com uma parede."""
    pass

class AtropelarHumanoError(AlarmeRobo):
    """Exceção levantada quando o robô atropela um humano."""
    pass

class EjetarSemHumanoError(AlarmeRobo):
    """Exceção levantada quando o robô tenta ejetar sem humano na carga."""
    pass

class ColetarSemHumanoError(AlarmeRobo):
    """Exceção levantada quando o robô tenta coletar sem humano à frente."""
    pass

class EjetarSemSaidaError(AlarmeRobo):
    """Exceção levantada quando o robô tenta ejetar sem estar na saída."""
    pass
