from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Tuple

from ambiente import (
    Ambiente,
    Direcao,
    DELTAS_POR_DIRECAO,
    LeituraSensor,
    ResultadoComando,
    SituacaoCarga,
    girar_esquerda,
)
from excecoes import (
    AlarmeRobo,
    AtropelarHumanoError,
    ColetarSemHumanoError,
    ColisaoComParedeError,
    EjetarSemHumanoError,
)

Posicao = Tuple[int, int]


def oposta(direcao: Direcao) -> Direcao:
    """Direção absoluta oposta a `direcao` (usada para voltar/backtrack)."""
    return Direcao((direcao.value + 2) % 4)


class ExploracaoImpossivelError(Exception):
    """Disparado se o robô esgotar toda a exploração possível sem achar o
    humano ou a saída. Pela especificação isso nunca deveria acontecer -
    existir este erro é só uma rede de segurança contra bug de lógica."""


# ==============================================================================
# MAPA INTERNO (memória construída SOMENTE a partir dos sensores)
# ==============================================================================

class MapaInterno:
    """Guarda, para cada posição já visitada, o que foi sentido em cada
    direção absoluta a partir dela. Nunca lê o mapa real."""

    def __init__(self) -> None:
        self._celulas: Dict[Posicao, Dict[Direcao, LeituraSensor]] = {}

    def registrar_leitura(self, pos: Posicao, direcao_frente: Direcao,
                           leitura: ResultadoComando) -> None:
        direcao_esquerda = girar_esquerda(direcao_frente)
        direcao_direita = oposta(direcao_esquerda)
        vizinhos = {
            direcao_esquerda: leitura.sensor_esquerdo,
            direcao_direita: leitura.sensor_direito,
            direcao_frente: leitura.sensor_frontal,
        }
        self._celulas.setdefault(pos, {}).update(vizinhos)

    def tipo_vizinho(self, pos: Posicao, direcao: Direcao) -> Optional[LeituraSensor]:
        return self._celulas.get(pos, {}).get(direcao)

    def procurar_direcao_com(self, pos: Posicao, tipo: LeituraSensor) -> Optional[Direcao]:
        """Se a célula `pos` já tem, entre as direções sentidas, uma com o
        tipo pedido (ex.: HUMANO ou SAIDA), devolve essa direção."""
        for direcao, sensor in self._celulas.get(pos, {}).items():
            if sensor == tipo:
                return direcao
        return None

    def encontrar_celula_com(self, tipo: LeituraSensor) -> Optional[Tuple[Posicao, Direcao]]:
        """Procura em TODO o mapa já conhecido uma célula de onde `tipo` foi
        sentido (usado para localizar a saída já vista anteriormente)."""
        for pos, vizinhos in self._celulas.items():
            for direcao, sensor in vizinhos.items():
                if sensor == tipo:
                    return pos, direcao
        return None

    def caminho_ate(self, origem: Posicao, destino: Posicao) -> Optional[List[Direcao]]:
        """BFS sobre as células já conhecidas como VAZIO. Devolve a lista de
        direções absolutas (uma por passo de 'A') do início ao fim, ou None
        se não houver caminho conhecido ainda."""
        if origem == destino:
            return []
        fila = deque([origem])
        veio_de: Dict[Posicao, Optional[Tuple[Posicao, Direcao]]] = {origem: None}
        encontrado = False
        while fila and not encontrado:
            atual = fila.popleft()
            for direcao, (dl, dc) in DELTAS_POR_DIRECAO.items():
                if self.tipo_vizinho(atual, direcao) != LeituraSensor.VAZIO:
                    continue
                vizinho = (atual[0] + dl, atual[1] + dc)
                if vizinho in veio_de:
                    continue
                veio_de[vizinho] = (atual, direcao)
                if vizinho == destino:
                    encontrado = True
                    break
                fila.append(vizinho)
        if destino not in veio_de:
            return None
        caminho: List[Direcao] = []
        cursor = destino
        while veio_de[cursor] is not None:
            anterior, direcao = veio_de[cursor]
            caminho.append(direcao)
            cursor = anterior
        caminho.reverse()
        return caminho


# ==============================================================================
# CÉREBRO DO ROBÔ
# ==============================================================================

class CerebroRobo:
    """Orquestra o ciclo LIGAR -> (decidir, enviar, atualizar)* -> ejetar.

    Uso:
        cerebro = CerebroRobo(Ambiente("labirinto.txt"))
        historico = cerebro.executar()   # roda até ejetar o humano
    """

    MAX_PASSOS = 200_000  # trava de segurança contra loop infinito por bug

    def __init__(self, ambiente: Ambiente) -> None:
        self._ambiente = ambiente
        self.mapa = MapaInterno()

        self.pos: Posicao = (0, 0)
        self.direcao: Direcao = Direcao.CIMA
        self.carregando_humano: bool = False
        self._finalizado: bool = False

        self._pilha: List[Posicao] = [self.pos]
        self._visitado = {self.pos}
        self._direcao_chegada: Dict[Posicao, Optional[Direcao]] = {self.pos: None}
        self._rota: List[Direcao] = []

        self._ultima_leitura: Optional[ResultadoComando] = None
        self.historico: List[Tuple[str, ResultadoComando]] = []

    # -------------------------------------------------------------- API pública

    def executar(self) -> List[Tuple[str, ResultadoComando]]:
        """Roda o ciclo completo até o humano ser ejetado. Devolve a lista de
        (comando, resultado) enviados, útil para depuração (o log oficial em
        CSV é responsabilidade do Ambiente / da Pessoa 1)."""
        self._ligar()
        passos = 0
        while not self._finalizado:
            passos += 1
            if passos > self.MAX_PASSOS:
                raise ExploracaoImpossivelError(
                    "Número máximo de passos excedido - provável bug de lógica "
                    "ou labirinto sem solução, o que contraria a especificação."
                )
            self.passo()
        return self.historico

    def passo(self) -> Tuple[str, ResultadoComando]:
        """Executa uma única iteração de decisão. Exposto separadamente para
        facilitar testes unitários passo a passo."""
        comando = self._decidir_proximo_comando()
        resultado = self._enviar(comando)
        self._processar_resultado(comando, resultado)
        return comando, resultado

    # -------------------------------------------------------------- internos

    def _ligar(self) -> None:
        resultado = self._ambiente.ligar()
        self.historico.append(("LIGAR", resultado))
        self._ultima_leitura = resultado
        self.mapa.registrar_leitura(self.pos, self.direcao, resultado)
        comando = "G"
        resultado = self._enviar(comando)
        self.direcao = girar_esquerda(self.direcao)
        self.mapa.registrar_leitura(self.pos, self.direcao, resultado)
        self._ultima_leitura = resultado
        self.historico.append((comando, resultado))

    def _enviar(self, comando: str) -> ResultadoComando:
        self._checar_seguranca_antes_de_enviar(comando)
        return self._ambiente.executar_comando(comando)

    def _checar_seguranca_antes_de_enviar(self, comando: str) -> None:
        leitura = self._ultima_leitura
        if leitura is None:
            return

        if comando == "A" and leitura.sensor_frontal == LeituraSensor.PAREDE:
            raise ColisaoComParedeError(
                "[algoritmo] Avanço bloqueado: última leitura de frente é PAREDE."
            )
        if comando == "A" and leitura.sensor_frontal == LeituraSensor.HUMANO:
            raise AtropelarHumanoError(
                "[algoritmo] Avanço bloqueado: última leitura de frente é HUMANO."
            )
        if comando == "P" and leitura.sensor_frontal != LeituraSensor.HUMANO:
            raise ColetarSemHumanoError(
                "[algoritmo] Coleta bloqueada: não há humano à frente na última leitura."
            )
        if comando == "P" and leitura.situacao_carga == SituacaoCarga.COM_HUMANO:
            raise ColetarSemHumanoError(
                "[algoritmo] Coleta bloqueada: já existe humano no compartimento."
            )
        if comando == "E" and leitura.situacao_carga != SituacaoCarga.COM_HUMANO:
            raise EjetarSemHumanoError(
                "[algoritmo] Ejeção bloqueada: compartimento sem humano."
            )

    def _processar_resultado(self, comando: str, resultado: ResultadoComando) -> None:
        self.historico.append((comando, resultado))
        self._ultima_leitura = resultado

        if comando == "G":
            self.direcao = girar_esquerda(self.direcao)
            self.mapa.registrar_leitura(self.pos, self.direcao, resultado)
            return

        if comando == "A":
            dl, dc = DELTAS_POR_DIRECAO[self.direcao]
            nova_pos = (self.pos[0] + dl, self.pos[1] + dc)
            if nova_pos not in self._visitado:
                self._visitado.add(nova_pos)
                self._direcao_chegada[nova_pos] = self.direcao
                self._pilha.append(nova_pos)
            elif self._pilha and self._pilha[-1] == self.pos:
                self._pilha.pop()
            self.pos = nova_pos
            self.mapa.registrar_leitura(self.pos, self.direcao, resultado)
            if self._rota:
                self._rota.pop(0)
            return

        if comando == "P":
            self.carregando_humano = True
            self.mapa.registrar_leitura(self.pos, self.direcao, resultado)
            return

        if comando == "E":
            self._finalizado = True
            return

    def _decidir_proximo_comando(self) -> str:
        leitura = self._ultima_leitura
        assert leitura is not None

        # 1) Humano bem na nossa frente -> coleta imediata
        if not self.carregando_humano and leitura.sensor_frontal == LeituraSensor.HUMANO:
            return "P"

        # 2) Saída bem na nossa frente e já com o humano -> ejeta imediato
        if self.carregando_humano and leitura.sensor_frontal == LeituraSensor.SAIDA:
            return "E"

        # 3) Humano conhecido nesta célula mas não na frente -> gira até ele
        if not self.carregando_humano:
            if self.mapa.procurar_direcao_com(self.pos, LeituraSensor.HUMANO) is not None:
                return "G"  # próxima leitura reavalia o alinhamento

        # 4) Saída conhecida nesta célula (mas não na frente) e já com humano
        if self.carregando_humano:
            if self.mapa.procurar_direcao_com(self.pos, LeituraSensor.SAIDA) is not None:
                return "G"

        # 5) Já existe uma rota planejada em andamento -> segue ela
        if self._rota:
            alvo = self._rota[0]
            return "A" if self.direcao == alvo else "G"

        # 6) Com humano e a saída já foi vista em outra célula -> traça rota
        if self.carregando_humano:
            achado = self.mapa.encontrar_celula_com(LeituraSensor.SAIDA)
            if achado is not None:
                pos_alvo, _ = achado
                caminho = self.mapa.caminho_ate(self.pos, pos_alvo)
                if caminho:
                    self._rota = caminho
                    alvo = self._rota[0]
                    return "A" if self.direcao == alvo else "G"

        # 7) Exploração DFS: existe vizinho livre e não visitado?
        direcao_nova = self._proxima_direcao_nao_visitada()
        if direcao_nova is not None:
            return "A" if self.direcao == direcao_nova else "G"

        # 8) Sem novidade por aqui -> backtrack (Trémaux)
        if len(self._pilha) > 1:
            direcao_volta = oposta(self._direcao_chegada[self.pos])
            return "A" if self.direcao == direcao_volta else "G"

        # 9) Backtrack esgotado sem achar humano/saída: não deveria acontecer
        raise ExploracaoImpossivelError(
            "Labirinto totalmente explorado sem encontrar o humano ou a "
            "saída - verifique a leitura dos sensores e a especificação."
        )

    def _proxima_direcao_nao_visitada(self) -> Optional[Direcao]:
        for direcao, (dl, dc) in DELTAS_POR_DIRECAO.items():
            if self.mapa.tipo_vizinho(self.pos, direcao) != LeituraSensor.VAZIO:
                continue
            vizinho = (self.pos[0] + dl, self.pos[1] + dc)
            if vizinho not in self._visitado:
                return direcao
        return None