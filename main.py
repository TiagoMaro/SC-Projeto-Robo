import sys

from ambiente import Ambiente
from robo import CerebroRobo
from excecoes import AlarmeRobo


def main():
    if len(sys.argv) < 2:
        print("Erro: informe o caminho do mapa.")
        print("Uso: python main.py <caminho_do_mapa>")
        sys.exit(1)

    caminho_mapa = sys.argv[1]
    
    try:
        ambiente = Ambiente(caminho_mapa)
        cerebro = CerebroRobo(ambiente)
        cerebro.executar()
        
        print("Execução concluída com sucesso.")
    
    except FileNotFoundError:
        print(f"Erro: arquivo de mapa não encontrado: {caminho_mapa}")
    
    except AlarmeRobo as e:
        print(f"Alarme de segurança do robô: {e}")
    
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    


if __name__ == "__main__":
    main()