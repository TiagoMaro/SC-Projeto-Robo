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

    def test_alarme_bloqueia_avanco_contra_humano_conhecido(self):
        """Checagem defensiva: se a última leitura de frente é HUMANO, o
        próprio robo.py deve barrar um 'A' antes mesmo de chamar o
        Ambiente (o comando certo ali seria 'P', não 'A')."""
        from excecoes import AtropelarHumanoError

        ambiente = _criar_ambiente(MAPA_HUMANO_AO_LADO)
        cerebro = CerebroRobo(ambiente)
        cerebro._ligar()
        object.__setattr__(cerebro._ultima_leitura, "sensor_frontal",
                            cerebro._ultima_leitura.sensor_frontal.__class__("HUMANO"))
        with self.assertRaises(AtropelarHumanoError):
            cerebro._enviar("A")

    def test_alarme_bloqueia_segunda_coleta_com_carga_cheia(self):
        """Não deve ser possível mandar 'P' de novo se o compartimento já
        está com um humano (a bateria só tem carga para uma tentativa)."""
        ambiente = _criar_ambiente(MAPA_HUMANO_AO_LADO)
        cerebro = CerebroRobo(ambiente)
        cerebro._ligar()
        object.__setattr__(cerebro._ultima_leitura, "sensor_frontal",
                            cerebro._ultima_leitura.sensor_frontal.__class__("HUMANO"))
        object.__setattr__(cerebro._ultima_leitura, "situacao_carga",
                            cerebro._ultima_leitura.situacao_carga.__class__("COM HUMANO"))
        with self.assertRaises(ColetarSemHumanoError):
            cerebro._enviar("P")

    def test_checagem_de_seguranca_antes_do_ligar_nao_bloqueia(self):
        """Antes do LIGAR não existe leitura anterior ainda; a checagem
        defensiva deve simplesmente não interferir (early-return)."""
        ambiente = _criar_ambiente(MAPA_HUMANO_AO_LADO)
        cerebro = CerebroRobo(ambiente)
        # Não chama cerebro._ligar(): _ultima_leitura continua None
        self.assertIsNone(cerebro._checar_seguranca_antes_de_enviar("A"))

    def test_excede_max_passos_lanca_exploracao_impossivel(self):
        """Rede de segurança contra bug de lógica: se o número de passos
        ultrapassar o limite configurado, a execução deve abortar com um
        erro claro em vez de rodar para sempre."""
        from robo import ExploracaoImpossivelError

        ambiente = _criar_ambiente(MAPA_DO_ENUNCIADO)
        cerebro = CerebroRobo(ambiente)
        cerebro.MAX_PASSOS = 1  # labirinto do enunciado precisa de bem mais que 1 passo
        with self.assertRaises(ExploracaoImpossivelError):
            cerebro.executar()

    def test_labirinto_sem_humano_lanca_exploracao_impossivel(self):
        """Se (por um mapa mal formado, fora do que a especificação
        garante) não houver humano nem saída alcançáveis, o robô deve
        esgotar a exploração e falhar de forma explícita, não travar."""
        from robo import ExploracaoImpossivelError

        # Sala fechada 1x1: robô não tem para onde ir e não há humano/saída
        ambiente = _criar_ambiente("XXX\nX!X\nXXX")
        cerebro = CerebroRobo(ambiente)
        with self.assertRaises(ExploracaoImpossivelError):
            cerebro.executar()


class TestMapaInterno(unittest.TestCase):
    """Testes unitários diretos na memória interna do robô (MapaInterno),
    isolados do Ambiente/CerebroRobo."""

    def test_encontrar_celula_com_devolve_none_quando_nao_ha_correspondencia(self):
        from ambiente import LeituraSensor
        from robo import MapaInterno

        mapa = MapaInterno()
        resultado = mapa.encontrar_celula_com(LeituraSensor.SAIDA)
        self.assertIsNone(resultado)

    def test_caminho_ate_mesma_posicao_devolve_lista_vazia(self):
        from robo import MapaInterno

        mapa = MapaInterno()
        origem = (0, 0)
        self.assertEqual(mapa.caminho_ate(origem, origem), [])


if __name__ == "__main__":  # pragma: no cover - ponto de entrada padrão, não é lógica de negócio
    unittest.main(verbosity=2)
