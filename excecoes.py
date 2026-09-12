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
    """Exceção levantada quando o robô tenta ejetar sem estar na saída.s"""
    pass
