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