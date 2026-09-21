import sys

import pytest

import main
from robo import CerebroRobo
from excecoes import AlarmeRobo, ColisaoComParedeError


MAPA_SIMPLES = (
    "XXXXX\n"
    "XS!.X\n"
    "X..@X\n"
    "XXXXX\n"
)


def _criar_mapa(tmp_path, texto=MAPA_SIMPLES):
    caminho = tmp_path / "mapa.txt"
    caminho.write_text(texto)
    return str(caminho)


def test_main_sem_argumentos_encerra_com_codigo_1(monkeypatch, capsys):
    """Sem o caminho do mapa, main() deve orientar o uso e sair com status 1."""
    monkeypatch.setattr(sys, "argv", ["main.py"])

    with pytest.raises(SystemExit) as excinfo:
        main.main()

    assert excinfo.value.code == 1
    saida = capsys.readouterr().out
    assert "informe o caminho do mapa" in saida
    assert "Uso: python main.py" in saida


def test_main_executa_com_sucesso_ate_o_fim(monkeypatch, capsys, tmp_path):
    """Caminho feliz: mapa válido, robô resgata o humano e main() reporta sucesso."""
    caminho_mapa = _criar_mapa(tmp_path)
    monkeypatch.setattr(sys, "argv", ["main.py", caminho_mapa])

    main.main()

    saida = capsys.readouterr().out
    assert "Execução concluída com sucesso." in saida


def test_main_arquivo_de_mapa_inexistente(monkeypatch, capsys, tmp_path):
    """Caminho para um mapa que não existe deve cair no except FileNotFoundError."""
    caminho_inexistente = str(tmp_path / "nao_existe.txt")
    monkeypatch.setattr(sys, "argv", ["main.py", caminho_inexistente])

    main.main()

    saida = capsys.readouterr().out
    assert "arquivo de mapa não encontrado" in saida
    assert caminho_inexistente in saida


def test_main_reporta_alarme_de_seguranca(monkeypatch, capsys, tmp_path):
    """Se o CerebroRobo levantar um AlarmeRobo, main() deve capturá-lo e
    reportar como alarme de segurança, sem deixar a exceção estourar."""
    caminho_mapa = _criar_mapa(tmp_path)
    monkeypatch.setattr(sys, "argv", ["main.py", caminho_mapa])

    def _executar_com_alarme(self):
        raise ColisaoComParedeError("colisão simulada para teste")

    monkeypatch.setattr(CerebroRobo, "executar", _executar_com_alarme)

    main.main()

    saida = capsys.readouterr().out
    assert "Alarme de segurança do robô" in saida
    assert "colisão simulada para teste" in saida


def test_main_reporta_erro_inesperado_generico(monkeypatch, capsys, tmp_path):
    """Qualquer outra exceção não prevista deve cair no except genérico,
    sem derrubar o processo."""
    caminho_mapa = _criar_mapa(tmp_path)
    monkeypatch.setattr(sys, "argv", ["main.py", caminho_mapa])

    def _executar_com_erro(self):
        raise ValueError("erro inesperado simulado")

    monkeypatch.setattr(CerebroRobo, "executar", _executar_com_erro)

    main.main()

    saida = capsys.readouterr().out
    assert "Ocorreu um erro inesperado" in saida
    assert "erro inesperado simulado" in saida


def test_alarmerobo_e_subclasse_de_exception():
    """Sanity check de hierarquia usada pelo except em main.py."""
    assert issubclass(AlarmeRobo, Exception)
