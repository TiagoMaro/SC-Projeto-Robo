Equipe:
Fábio Carvalho de Almeida RA: 2024101059
Tiago Machado da Rosa RA: 2024101751
Victor Hugo Mondequi Viana RA: 2024100142



3 - ARQUITETURA
    Possui uma classe própria Ambiente, que gerencia toda a parte do mapa.
    Possui acesso completo do mapa para auxiliar o robô na locomoção, foi realizada essa separação do mapa para Ambiente não para o Robô para evitar trapaças por parte do robô na hora de se locomover dentro do labirinto.
    Método ligar(), devolve a leitura dos sensores.
    Método executar_comando(), devolvendo um ResultadoComando, dando autonômia para o robô utiliza-los e tomar suas próprias decisões.
    - Alarme 1 - ColisaoComParedeError - utilizado para prevenir que o robô execute o comando "A" estando de frente para uma parede.
    - Alarme 2 - AtropelarHumanoError - utilizado para evitar que o robô execute o comando "A" estando de frente para o humano.
    - Alarme 3 - EjetarSemHumanoError - utilizado para garantir que o robô execute o comando "E" quando estiver com o humano.
    - Alarme 4 - EjetarSemSaidaError - utilizado para garantir que o robô execute o comando "E" apenas quando estiver de frente para saída.
    - Alarme 5 - ColetarSemHumanoError - utilizado para prevenir que o robô execute o comando "P" de coleta sem estar de frente para o humano.
    Registra logs automaticamente a cada passo do robô sem precisar de uma chamada extra para quem utiliza a classe.
    O log é gerado na mesma pasta do caminho que o arquivo do mapa está.

6 - DECISÕES DE PROJETO E JUSTIFICATIVA
    O Log é escrito logo após o robô executar uma ação para nos ajudar na hora de depuração de erros, e também para caso algo inesperado aconteça e o processo seja interrompido termos um controle do que exatamente aconteceu com o robô, e qual foi o caminho que ele percorreu.
    Optou-se por adicionar 2 alarmes para ejetar, pois assim cada erro tem apenas uma responsabilidade para exercer e também facilita na hora de visualizar o erro. Se o robô tentar ejetar sem a carga ele apenas vai aparecer o erro EjetarSemHumanoError, agora se o robô estiver com carga mas não estiver de frente para saída ele vai emitir o erro EjetarSemSaidaError, facilitando na hora da leitura de erros.