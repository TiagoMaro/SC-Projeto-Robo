import pytest
from ambiente import Ambiente, Direcao, calcular_proxima_posicao, girar_esquerda, carregar_mapa
from excecoes import ColetarSemHumanoError, ColisaoComParedeError, AtropelarHumanoError, EjetarSemHumanoError

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

def test_coletar_sem_humano_lanca_excecao(tmp_path):
    caminho_arquivo = tmp_path / "labirinto_teste.txt"
    mapa_exemplo = ("XXX\n"
                    "X!X\n"
                    "XXX")
    caminho_arquivo.write_text(mapa_exemplo)

    ambiente = Ambiente(str(caminho_arquivo))

    with pytest.raises(ColetarSemHumanoError):
        ambiente.executar_comando('P')