import pyttsx3
import speech_recognition as sr
import openai
import yaml
import requests
import re




with open('config.yml', 'r') as arquivo:
    dados = yaml.safe_load(arquivo)

openai.api_key = dados['open_ia']['api']

# Inicialização do sintetizador de voz
speak = pyttsx3.init()

# Configura a voz para português
for voz in speak.getProperty('voices'):
    # Verifica se a voz tem pelo menos dois idiomas e se o segundo idioma é 'pt'
    if len(voz.languages) > 1 and 'pt' in voz.languages[1]:
        speak.setProperty('voice', voz.id)
        break

speak.setProperty("rate", 180)
speak.setProperty("volume", 1)

# Inicialização do reconhecedor de voz
r = sr.Recognizer()

def falar(mensagem):
    speak.say(mensagem)
    speak.runAndWait()

def ouvir():
    with sr.Microphone() as source:
        print("Ajustando o ruído de fundo. Por favor, aguarde...")
        r.adjust_for_ambient_noise(source)
        print("Pronto! Pode falar.")
        falar("Pronto! Pode falar.")
        audio = r.listen(source)
    try:
        texto = r.recognize_google(audio, language='pt-BR')
        print("Você disse: " + texto)
        return texto
    except sr.UnknownValueError:
        print("Desculpe, não consegui entender.")
        falar("Desculpe, não consegui entender.")
        return None
    except sr.RequestError as e:
        print("Erro ao se comunicar com o serviço de reconhecimento; {0}".format(e))
        falar("Desculpe, houve um erro de conexão.")
        return None

currency_mapping = {
    'dólar': 'USD',
    'dolar': 'USD',
    'usd': 'USD',
    'reais': 'BRL',
    'real': 'BRL',
    'brl': 'BRL',
    'euro': 'EUR',
    'eur': 'EUR',
    'iene': 'JPY',
    'jpy': 'JPY',
    'libra': 'GBP',
    'gbp': 'GBP',
    'franco': 'CHF',
    'chf': 'CHF',
    'yuan': 'CNY',
    'cny': 'CNY',
    'peso': 'ARS',
    'ars': 'ARS',
}

def obter_resposta(entrada_usuario):
    try:
        entrada_usuario = entrada_usuario.lower()

        # Verificar se o usuário pediu por notícias
        if "notícia" in entrada_usuario or "notícias" in entrada_usuario:
            match = re.search(r'(?:notícia(?:s)? (?:sobre|de|do|da)|notícias|notícia) (.+)', entrada_usuario)
            if match:
                termo_busca = match.group(1)
            else:
                termo_busca = "geral"
            return obter_noticias(termo_busca)

            # Verificar se o usuário pediu por conversão de moedas
        if "converte" or 'converter' in entrada_usuario and ("para" in entrada_usuario or "em" in entrada_usuario):
            # Expressão regular para extrair quantidade, moeda origem e moeda destino
            match = re.search(r'converte\s+([^\s]+)\s+([^\s]+)(?:\s+(?:para|em)\s+([^\s]+))?', entrada_usuario)
            if match:
                quantidade_str = match.group(1)
                moeda_origem_nome = match.group(2)
                moeda_destino_nome = match.group(3) if match.group(3) else ''

                # Normalizar quantidade
                quantidade_str = quantidade_str.replace('r$', '').replace('$', '').replace('€', '').replace('£',
                                                                                                                '').replace(
                    ',', '.')
                try:
                    quantidade = float(quantidade_str)
                except ValueError:
                    return "Desculpe, não consegui entender o valor a ser convertido."

                # Obter códigos das moedas
                moeda_origem = currency_mapping.get(moeda_origem_nome.lower())
                if moeda_origem is None:
                    return f"Desculpe, não reconheço a moeda '{moeda_origem_nome}'."

                moeda_destino = currency_mapping.get(moeda_destino_nome.lower())
                if moeda_destino is None or moeda_destino == '':
                    return "Desculpe, você precisa especificar a moeda de destino."

                return converter_moeda(moeda_origem, moeda_destino, quantidade)
            else:
                return "Desculpe, não consegui entender o comando de conversão. Por favor, tente novamente."

        # Caso contrário, usar a API da OpenAI
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Você é um assistente virtual que fala português do Brasil."},
                {"role": "user", "content": entrada_usuario}
            ],
            max_tokens=150
        )
        mensagem = response['choices'][0]['message']['content'].strip()
        return mensagem
    except openai.error.RateLimitError:
        return "Você excedeu sua cota de uso da API. Por favor, verifique seu plano de cobrança."
    except openai.error.OpenAIError as e:
        return f"Erro ao obter a resposta: {str(e)}"


# Loop principal do programa
def executar_assistente():
    while True:
        entrada = ouvir()
        if entrada:
            if entrada.lower() in ["sair", "encerrar", "tchau"]:
                falar("Até logo! Foi um prazer ajudar.")
                print("Até logo! Foi um prazer ajudar.")
                break
            resposta = obter_resposta(entrada)
            print("Assistente: " + resposta)
            falar(resposta)

def converter_moeda(moeda_origem, moeda_destino, quantidade):
    with open('config.yml', 'r') as arquivo:
        dados = yaml.safe_load(arquivo)

    api_key = dados['currencyapi']['api']
    url = f"https://api.currencyconverterapi.com/api/v7/convert?q={moeda_origem}_{moeda_destino}&compact=ultra&apiKey={api_key}"

    try:
        # Fazer a requisição para a API
        resposta = requests.get(url)
        dados = resposta.json()

        # Verifica se a conversão foi encontrada
        if f"{moeda_origem}_{moeda_destino}" in dados:
            taxa_conversao = dados[f"{moeda_origem}_{moeda_destino}"]
            resultado = quantidade * taxa_conversao
            return f"{quantidade} {moeda_origem} equivale a {resultado:.2f} {moeda_destino}."
        else:
            return "Não foi possível realizar a conversão."
    except Exception as e:
        return f"Erro ao consultar a API: {str(e)}"


def obter_clima(cidade):
    with open('config.yml', 'r') as arquivo:
        dados = yaml.safe_load(arquivo)

    api_weather = dados['openweathermap']['api']
    url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={api_weather}&lang=pt&units=metric"
    resposta = requests.get(url)

    if resposta.status_code == 200:
        info=resposta.json()
        descricao_clima = info['weather'][0]['description']
        temperatura = info['main']['temp']
        mensagem = f"O clima em {cidade} é de {descricao_clima} com temperatura de {temperatura}°C."
        return mensagem
    else:
        return "Desculpe, não consegui obter o clima agora."


def obter_noticias(termo_busca):
    with open('config.yml', 'r') as arquivo:
        dados = yaml.safe_load(arquivo)
    api_key = dados['newsapi']['api']
    url = f"https://newsapi.org/v2/everything?q={termo_busca}&language=pt&sortBy=publishedAt&apiKey={api_key}"

    try:
        # Fazer a requisição para a API
        resposta = requests.get(url)
        dados = resposta.json()

        # Verifica se a API retornou resultados
        if dados["status"] == "ok" and dados["totalResults"] > 0:
            noticias = dados["articles"][:1]  # Pegamos as 5 primeiras notícias
            resposta_noticias = []

            for noticia in noticias:
                titulo = noticia['title']
                descricao = noticia['description']
                resposta_noticias.append(f"Título: {titulo}\nDescrição: {descricao}\n")

            return "\n\n".join(resposta_noticias)
        else:
            return "Desculpe, não encontrei notícias sobre esse assunto."
    except Exception as e:
        return f"Erro ao consultar a API de notícias: {str(e)}"


executar_assistente()
