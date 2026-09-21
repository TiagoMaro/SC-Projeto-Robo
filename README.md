# Robô de Resgate em Labirinto

Software embarcado para um robô que explora um labirinto desconhecido usando
apenas os sensores de frente, esquerda e direita, resgata um humano perdido e
o leva até a saída, gerando um log CSV auditável de toda a operação.

**Equipe**
- Fábio Carvalho de Almeida — RA: 2024101059
- Tiago Machado da Rosa — RA: 2024101751
- Victor Hugo Mondequi Viana — RA: 2024100142

---

## 1. Como o projeto funciona

O sistema é dividido em duas partes que só se enxergam por uma interface bem
estreita:

- **`ambiente.py` — o simulador.** Carrega o mapa de um
  arquivo de texto, sabe a posição e a orientação reais do robô, e é o único
  lugar que tem acesso ao mapa completo. Expõe só dois métodos para fora:
  `ligar()` e `executar_comando(comando)`. Cada um devolve um
  `ResultadoComando` com as 3 leituras de sensor (esquerda, frente, direita) e
  a situação da carga — e cada chamada já grava automaticamente uma linha no
  log CSV.
- **`robo.py` — o cérebro embarcado.** É o algoritmo de busca.
  Ele nunca olha o mapa real: só conhece o que os sensores foram
  reportando, e vai montando um mapa próprio (`MapaInterno`) conforme explora.
  A estratégia é uma DFS com backtracking para achar o
  humano.
- **`excecoes.py`** define os 5 alarmes de segurança.
- **`main.py`** é quem conecta as duas pontas: cria o
  `Ambiente` a partir de um arquivo de mapa, cria o `CerebroRobo` em cima dele
  e roda a exploração até o fim.

### Formato do mapa (arquivo de entrada)

| Caractere | Significado |
|---|---|
| `X` | parede |
| `.` | espaço livre |
| `!` | posição inicial do robô (tratada como vazio nos sensores) |
| `@` | humano |
| `S` | saída |

O robô sempre começa virado para cima.

### Comandos e sensores

| Comando | Efeito |
|---|---|
| `LIGAR` | liga o robô, só lê os sensores na posição inicial |
| `A` | avança uma posição |
| `G` | gira 90° à esquerda (anti-horário) |
| `P` | pega o humano imediatamente à frente |
| `E` | ejeta o humano para fora do labirinto |

Cada sensor enxerga só a célula imediatamente à frente/esquerda/direita e
retorna um entre `PAREDE`, `VAZIO`, `HUMANO` ou `SAÍDA`.

### Log gerado

Um `.csv` (UTF-8, sem cabeçalho) com o mesmo nome do arquivo de mapa, com uma
linha por comando executado:

```
comando,sensor_esquerdo,sensor_direito,sensor_frontal,situacao_carga
```

Exemplo:
```
LIGAR,VAZIO,VAZIO,SAÍDA,SEM CARGA
G,PAREDE,SAÍDA,VAZIO,SEM CARGA
...
E,VAZIO,VAZIO,HUMANO,SEM CARGA
```

### Alarmes de segurança

| Alarme | Dispara quando... |
|---|---|
| `ColisaoComParedeError` | o robô tenta avançar (`A`) contra uma parede |
| `AtropelarHumanoError` | o robô tenta avançar (`A`) contra o humano |
| `ColetarSemHumanoError` | o robô tenta coletar (`P`) sem humano à frente |
| `EjetarSemHumanoError` | o robô tenta ejetar (`E`) sem humano na carga |
| `EjetarSemSaidaError` | o robô tenta ejetar (`E`) sem estar de frente para a saída |

Todos herdam de `AlarmeRobo`. Cada alarme é checado duas vezes: uma vez pelo
próprio `Ambiente` (a fonte da verdade) e, redundantemente, pelo `robo.py`
antes mesmo de enviar o comando, que proporciona uma segunda rede de segurança.

---

## 2. Como rodar

### Pré-requisitos
```bash
pip install -r requirements.txt
```

### Rodar o robô em um mapa
```bash
python main.py caminho/para/labirinto.txt
```
Isso gera `caminho/para/labirinto.csv` com o log completo da operação no mesmo local que está localizado o mapa utilizado para o teste. O mapa deve ser um `.txt` seguindo a codificação de caracteres da seção 1.

### Rodar os testes
```bash
pytest tests/ -v
```

### Rodar os testes com relatório de cobertura
```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## 3. Decisões de projeto

- **5 alarmes em vez de 4**: a ejeção foi separada em `EjetarSemHumanoError` e
  `EjetarSemSaidaError` para que cada
  exceção tenha uma responsabilidade só, facilitando a leitura do log de erros.
- **Log escrito comando a comando**: garante que,
  se a execução for interrompida no meio, o log parcial gerado até ali
  continua válido para auditoria.
- **Log sempre começa zerado por execução**: evita que um `.csv` de uma
  rodada anterior sobre o mesmo mapa seja acidentalmente misturado com o log
  da rodada atual.

## 4. Cobertura de testes

100% de cobertura em `ambiente.py`, `excecoes.py`, `main.py` e `robo.py`
(348/348 statements, medido com `pytest-cov`). As únicas linhas fora do
cálculo são os dois guardas de ponto de entrada `if __name__ == "__main__":`
(em `main.py` e em `tests/test_robo.py`), marcados com `# pragma: no cover`
por não serem lógica de negócio — apenas o idioma padrão do Python para
permitir importar o módulo sem executá-lo.
