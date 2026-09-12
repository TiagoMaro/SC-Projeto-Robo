import os
import tempfile
import unittest

from ambiente import Ambiente
from excecoes import AlarmeRobo, ColisaoComParedeError, ColetarSemHumanoError, EjetarSemHumanoError
from robo import CerebroRobo


def _criar_ambiente(mapa_texto: str) -> Ambiente:
    """Escreve o mapa em um arquivo temporário e devolve um Ambiente real
    apontando para ele (evita depender de mocks para os testes principais)."""
    arquivo = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, encoding="utf-8"
    )
    arquivo.write(mapa_texto.strip("\n") + "\n")
    arquivo.close()
    return Ambiente(arquivo.name)


MAPA_DO_ENUNCIADO = """
XXXSXXX
X..!..X
X.XXXXX
X.....X
XXXXX.X
X.....X
X.XXX.X
X.X..@X
XXXXXXX
"""

MAPA_COM_LOOP = """
XXXXXXX
XS....X
X.XXX.X
X.X.!.X
X.X.X.X
X...X.X
X.XXX.X
X....@X
XXXXXXX
"""

MAPA_HUMANO_AO_LADO = """
XXXXX
XS!@X
XXXXX
"""


class TestCerebroRobo(unittest.TestCase):

    def test_encontra_e_resgata_humano_labirinto_do_enunciado(self):
        """Caso de teste principal: o robô deve achar o humano e ejetá-lo na
        saída, usando o Ambiente real e o mapa de exemplo do professor."""
        ambiente = _criar_ambiente(MAPA_DO_ENUNCIADO)
        cerebro = CerebroRobo(ambiente)
        historico = cerebro.executar()

        comandos_enviados = [c for c, _ in historico]
        self.assertIn("P", comandos_enviados)
        self.assertIn("E", comandos_enviados)
        self.assertTrue(cerebro._finalizado)
        self.assertLess(comandos_enviados.index("P"), comandos_enviados.index("E"))

    def test_funciona_em_labirinto_com_loop(self):
        """DFS puro (mão-na-parede) travaria em labirintos com ciclos; este
        teste garante que o backtracking não entra em loop infinito."""
        ambiente = _criar_ambiente(MAPA_COM_LOOP)
        cerebro = CerebroRobo(ambiente)
        historico = cerebro.executar()
        self.assertIn("E", [c for c, _ in historico])

    def test_gira_antes_de_coletar_humano_ao_lado(self):
        """O algoritmo NUNCA deve mandar 'P' com o humano ao lado - precisa
        girar até ele estar de frente primeiro (senão o próprio Ambiente
        já levantaria ColetarSemHumanoError)."""
        ambiente = _criar_ambiente(MAPA_HUMANO_AO_LADO)
        cerebro = CerebroRobo(ambiente)
        historico = cerebro.executar()  # não deve levantar nenhuma exceção
        comandos_enviados = [c for c, _ in historico]
        self.assertIn("P", comandos_enviados)
        self.assertIn("E", comandos_enviados)

    def test_alarme_bloqueia_avanco_contra_parede_conhecida(self):
        """Checagem defensiva redundante: se por bug o algoritmo tentasse
        avançar sabendo (pela última leitura) que há parede à frente, o
        próprio robo.py deve barrar isso antes de chamar o Ambiente."""
        ambiente = _criar_ambiente(MAPA_HUMANO_AO_LADO)
        cerebro = CerebroRobo(ambiente)
        cerebro._ligar()
        object.__setattr__(cerebro._ultima_leitura, "sensor_frontal",
                            cerebro._ultima_leitura.sensor_frontal.__class__("PAREDE"))
        with self.assertRaises(ColisaoComParedeError):
            cerebro._enviar("A")

    def test_alarme_bloqueia_ejecao_sem_humano(self):
        """Não deve ser possível mandar 'E' se a última leitura indica que o
        compartimento está vazio."""
        ambiente = _criar_ambiente(MAPA_HUMANO_AO_LADO)
        cerebro = CerebroRobo(ambiente)
        cerebro._ligar()
        with self.assertRaises(EjetarSemHumanoError):
            cerebro._enviar("E")

    def test_alarme_bloqueia_coleta_sem_humano_a_frente(self):
        """Não deve ser possível mandar 'P' se a última leitura de frente não
        é HUMANO."""
        ambiente = _criar_ambiente(MAPA_COM_LOOP)
        cerebro = CerebroRobo(ambiente)
        cerebro._ligar()
        with self.assertRaises(ColetarSemHumanoError):
            cerebro._enviar("P")


if __name__ == "__main__":
    unittest.main(verbosity=2)
