import pytest
from ambiente import Ambiente, Direcao, LeituraSensor, calcular_proxima_posicao, girar_esquerda, carregar_mapa
from excecoes import ColetarSemHumanoError, ColisaoComParedeError, AtropelarHumanoError, EjetarSemHumanoError, EjetarSemSaidaError

# TESTE UNITÁRIO AVANÇAR PARA DIREITA
def test_avancar_para_direita():
    resultado = calcular_proxima_posicao((3, 5), Direcao.DIREITA)
    assert resultado == (3, 6)

# TESTE UNITÁRIO GIRAR ESQUERDA
def test_girar_esquerda():
    resultado = girar_esquerda(Direcao.CIMA)
    assert resultado == Direcao.ESQUERDA

def test_carregar_mapa_le_arquivo_corretamente(tmp_path):
    # tmp_path é uma pasta temporária, criada automaticamente pelo pytest
    caminho_arquivo = tmp_path / "labirinto_teste.txt"

    # Um mini-mapa de exemplo
    mapa_exemplo = ("XXXXX\n"
                    "X   X\n"
                    "X X X\n"
                    "X   X\n"
                    "XXXXX")

    # Escrevendo o mapa de exemplo no arquivo temporário
    caminho_arquivo.write_text(mapa_exemplo)
    
    resultado = carregar_mapa(str(caminho_arquivo))
    
    assert resultado == [    
            ['X', 'X', 'X', 'X', 'X'],
            ['X', ' ', ' ', ' ', 'X'],
            ['X', ' ', 'X', ' ', 'X'],
            ['X', ' ', ' ', ' ', 'X'],
            ['X', 'X', 'X', 'X', 'X']  
    ]

def test_colisao_com_parede_lanca_excecao(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    posicao_antes = ambiente.posicao_atual

    with pytest.raises(ColisaoComParedeError):
        ambiente.executar_comando('A')

def test_atropelar_humano_lanca_excecao(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X@X\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    posicao_antes = ambiente.posicao_atual

    with pytest.raises(AtropelarHumanoError):
        ambiente.executar_comando('A')

def test_ejetar_sem_humano_lanca_excecao(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))

    with pytest.raises(EjetarSemHumanoError):
        ambiente.executar_comando('E') 
        
def test_ejetar_sem_saida_lanca_excecao(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X@X\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    ambiente.executar_comando('P')

    with pytest.raises(EjetarSemSaidaError):
        ambiente.executar_comando('E')

def test_coletar_sem_humano_lanca_excecao(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))

    with pytest.raises(ColetarSemHumanoError):
        ambiente.executar_comando('P')
        
def test_avancar_sem_colisao_atualiza_posicao(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X.X\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    assert ambiente.posicao_atual == (2, 1)
    resultado = ambiente.executar_comando('A')
    assert ambiente.posicao_atual == (1, 1)
    assert resultado.sensor_frontal == LeituraSensor.PAREDE
    
def test_girar_depois_avancar_contra_parede_lanca_excecao(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X.X\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    assert ambiente.posicao_atual == (2, 1)
    assert ambiente.direcao_atual == Direcao.CIMA
    ambiente.executar_comando('G')
    assert ambiente.direcao_atual == Direcao.ESQUERDA
    with pytest.raises(ColisaoComParedeError):
        ambiente.executar_comando('A')

def test_ligar_le_sensores_iniciais_sem_mover_robo(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X.X\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    posicao_antes = ambiente.posicao_atual
    direcao_antes = ambiente.direcao_atual
    resultado = ambiente.ligar()

    assert ambiente.posicao_atual == posicao_antes
    assert ambiente.direcao_atual == direcao_antes
    assert resultado.sensor_frontal == LeituraSensor.VAZIO
    assert resultado.sensor_esquerdo == LeituraSensor.PAREDE
    assert resultado.sensor_direito == LeituraSensor.PAREDE
    
def test_registrar_log_gera_arquivo_csv_correto(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X.X\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    ambiente.ligar()
    ambiente.executar_comando('A')

    assert ambiente.caminho_log.exists()

    with open(ambiente.caminho_log, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
        assert linhas[0].strip() == "LIGAR,PAREDE,PAREDE,VAZIO,SEM CARGA"
        assert linhas[1].strip() == "A,PAREDE,PAREDE,PAREDE,SEM CARGA"
        assert len(linhas) == 2

def test_nova_execucao_nao_acumula_log_de_execucao_anterior(tmp_path):
    """Se já existir um .csv de uma execução anterior sobre o mesmo mapa,
    uma nova instância de Ambiente deve começar com o log limpo, não
    concatenar as linhas antigas com as novas."""
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X.X\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    # Primeira execução: gera um log com 2 linhas (LIGAR + A)
    ambiente_1 = Ambiente(str(caminho_arquivo))
    ambiente_1.ligar()
    ambiente_1.executar_comando('A')
    assert ambiente_1.caminho_log.read_text(encoding='utf-8').count('\n') == 2

    # Segunda execução sobre o MESMO arquivo de mapa: o log antigo não pode
    # ser herdado, mesmo antes de qualquer comando ser enviado.
    ambiente_2 = Ambiente(str(caminho_arquivo))
    assert ambiente_2.caminho_log.read_text(encoding='utf-8') == ""

    ambiente_2.ligar()
    with open(ambiente_2.caminho_log, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    assert len(linhas) == 1
    assert linhas[0].strip() == "LIGAR,PAREDE,PAREDE,VAZIO,SEM CARGA"

def test_sensor_frontal_le_humano_logo_apos_ejetar(tmp_path):
    """Conforme o exemplo do enunciado (última linha do log de referência:
    'E,VAZIO,VAZIO,HUMANO,SEM CARGA'), o humano recém-ejetado ocupa a célula
    da saída, então a PRÓXIMA leitura do sensor frontal deve acusar HUMANO,
    não mais SAÍDA."""
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XSX\n"
                    "X@X\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    ambiente.executar_comando('P')   # humano já está de frente: coleta
    ambiente.executar_comando('A')   # avança pra célula do humano (agora livre)
    resultado = ambiente.executar_comando('E')  # saída fica de frente: ejeta

    assert resultado.sensor_frontal == LeituraSensor.HUMANO
    assert resultado.situacao_carga.value == "SEM CARGA"

def test_mapa_sem_posicao_inicial_lanca_value_error(tmp_path):
    """Mapa mal formado, sem o caractere '!', deve falhar de forma clara ao
    instanciar o Ambiente, em vez de comportamento indefinido depois."""
    caminho_arquivo = tmp_path / "labirinto_sem_robo.txt"
    mapa_exemplo = ("XXX\n"
                    "X.X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    with pytest.raises(ValueError, match="Posição inicial não encontrada"):
        Ambiente(str(caminho_arquivo))

def test_sensor_fora_dos_limites_do_mapa_e_tratado_como_parede(tmp_path):
    """Robô posicionado na borda: células fora da matriz (linha/coluna
    negativa ou além do tamanho do mapa) devem ser lidas como PAREDE, nunca
    estourar um IndexError."""
    caminho_arquivo = tmp_path / "labirinto_borda.txt"
    # Linha 1 é mais curta que as outras -> testa também limite de coluna
    mapa_exemplo = ("!.\n"
                    "..X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    resultado = ambiente.ligar()

    # Robô em (0,0) virado pra CIMA: frente e esquerda saem do mapa
    assert resultado.sensor_frontal == LeituraSensor.PAREDE
    assert resultado.sensor_esquerdo == LeituraSensor.PAREDE

def test_caractere_desconhecido_no_mapa_lanca_value_error(tmp_path):
    """Um caractere fora da codificação especificada (@, S, X, ., !) deve
    falhar explicitamente ao ser sentido, em vez de ser ignorado."""
    caminho_arquivo = tmp_path / "labirinto_invalido.txt"
    # '?' fica bem na frente do robô (que começa virado pra CIMA)
    mapa_exemplo = ("XXX\n"
                    "X?X\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))
    with pytest.raises(ValueError, match="Caractere desconhecido"):
        ambiente.ligar()