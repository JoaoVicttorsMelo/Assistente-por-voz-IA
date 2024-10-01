import pyttsx3
import speech_recognition as sr
import openai
import yaml
import requests



def chamar_yml(nome,api):
    arquivo_yml = 'config.yml'
    with open(arquivo_yml, 'r') as arquivo:
        dados = yaml.safe_load(arquivo)
    return dados[nome][api]


dados = chamar_yml('open_ia','api')
openai.api_key  = dados

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

def obter_resposta(entrada_usuario):
    try:

        # Verificar se o usuário pediu por notícias
        if "notícias" in entrada_usuario.lower():
            # Extrair o tema das notícias da entrada do usuário
            palavras = entrada_usuario.split()
            if len(palavras) > 1:
                termo_busca = palavras[-1]  # Pegamos a última palavra como tema
            else:
                termo_busca = "geral"  # Um tema genérico se não for especificado

            # Chamar a função de obter notícias
            return obter_noticias(termo_busca)


        if "converter" in entrada_usuario.lower() and "para" in entrada_usuario.lower():
            # Extrair moedas e quantidade da entrada do usuário
            palavras = entrada_usuario.split()
            moeda_origem = palavras[palavras.index("converter") + 1].upper()
            quantidade = float(palavras[palavras.index("converter") + 2])
            moeda_destino = palavras[palavras.index("para") + 1].upper()
            # Chamar a função de conversão de moedas
            return converter_moeda(moeda_origem, moeda_destino, quantidade)


        if 'clima' in entrada_usuario.lower():
            cidade = entrada_usuario.split('clima em')[-1].strip()
            return obter_clima(cidade)

        # Formata o prompt que será enviado ao modelo
        prompt = f"Usuário: {entrada_usuario}\nAssistente:"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Você é um assistente virtual que fala português do Brasil."},
                {"role": "user", "content": prompt}  # Enviando o prompt formatado
            ]
        )
        mensagem = response['choices'][0]['message']['content']
        return mensagem
    except openai.error.OpenAIError as e:
        print(f"Erro na API do OpenAI: {e}")
        falar("Desculpe, houve um erro ao se comunicar com a API.")
        return "Desculpe, houve um problema ao obter a resposta."


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
    dado = chamar_yml('currencyapi','api')

    api_key = dado
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
    dados = chamar_yml('openweathermap','api')
    api_weather = dados
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
    dados = chamar_yml('newsapi','api')
    api_key = dados  # Substitua pela sua chave da API
    url = f"https://newsapi.org/v2/everything?q={termo_busca}&language=pt&sortBy=publishedAt&apiKey={api_key}"

    try:
        # Fazer a requisição para a API
        resposta = requests.get(url)
        dados = resposta.json()

        # Verifica se a API retornou resultados
        if dados["status"] == "ok" and dados["totalResults"] > 0:
            noticias = dados["articles"][:5]  # Pegamos as 5 primeiras notícias
            resposta_noticias = []

            for noticia in noticias:
                titulo = noticia['title']
                descricao = noticia['description']
                url_noticia = noticia['url']
                resposta_noticias.append(f"Título: {titulo}\nDescrição: {descricao}\nLink: {url_noticia}\n")

            return "\n\n".join(resposta_noticias)
        else:
            return "Desculpe, não encontrei notícias sobre esse assunto."
    except Exception as e:
        return f"Erro ao consultar a API de notícias: {str(e)}"


executar_assistente()
