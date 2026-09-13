class AlarmeRobo(Exception):
    """Classe base para todos os alarmes de segurança do robô."""

class ColisaoComParedeError(AlarmeRobo):
    """Exceção levantada quando o robô colide com uma parede."""

class AtropelarHumanoError(AlarmeRobo):
    """Exceção levantada quando o robô atropela um humano."""
    
class EjetarSemSaidaError(AlarmeRobo):
    """Exceção levantada quando o robô tenta ejetar sem estar na saída."""

class EjetarSemHumanoError(AlarmeRobo):
    """Exceção levantada quando o robô tenta ejetar sem humano na carga."""

class ColetarSemHumanoError(AlarmeRobo):
    """Exceção levantada quando o robô tenta coletar sem humano à frente."""
    