#-----------------------------------------------------------------------#
#									#									#
#   SCRIPT PYTHON PARA WEB SERVICE | WEBSERVER | CONNECTION TO WEBAPP 		#
#									#
# by: Paulo correia | Marcelo Gonçalves									#
#-----------------------------------------------------------------------#

# bibliotecas necessárias a execução do webservice
import os
import shutil
from flask import Flask, Response, request, abort, render_template_string, send_from_directory, render_template, redirect, url_for
from PIL import Image
from io import StringIO
import sqlite3 as sql


#inicio do webserver e respetiva pasta da pagina web
app = Flask(__name__, template_folder='template')

#Chave secreta do Server
SECRET_KEY = 'pl/mrcl/stgl/t'

#ajudas necessárias
HOST = "172.20.10.2"
PORTA= 6969
#tamanho da foto 
WIDTH = 640
HEIGHT = 360
#--------------------------------------------------------------------------------------------------------
#Funfões necessárias para login and register
#--------------------------------------------------------------------------------------------------------
def check_pssw(hashed_pssw, mail_pssw): #encriptação da password
    return hashed_pssw == mail_pssw

def validate(mail, pssw): #função de validação do login
    con = sql.connect('static/database.db') #abertura da base de dados
    completion = False
    with con:
                cur = con.cursor()
                cur.execute("SELECT * FROM clientes") #query SQL para ver base de dados
                rows = cur.fetchall()
                for row in rows:
                    dbmail = row[2]
                    dbpssw = row[3]
                    if dbmail==mail:
                        completion=check_pssw(dbpssw, pssw)
    return completion

def check(name, mail, pssw, date): #funçºao para validar o registo de utilizadores
    con = sql.connect('static/database.db')#abertura da base de dados
    unique = True
    cur = con.cursor()

    if pssw != "": #caso sejam preenchidos os campos vai a base de dados tentar fazer match
        with con:
            cur.execute("SELECT * FROM clientes") #query SQL para ver a base de daods
            rows = cur.fetchall()
            for row in rows:
                dbmail = row[2]
                if mail == dbmail:
                    unique = False
    else: #se nao fizer match ele cria um novo utilizador
        unique = False
                
    if unique == True:
        sql1 = "INSERT INTO clientes(name,mail,pssw,date) " \
              "VALUES(?,?,?,?)" #query SQL para inserir da base de dados o novo utilizador
        info = (name, mail, pssw, date)
        cur.execute(sql1, info)
        con.commit()
        cur.close()
        con.close() #fecho da base de dados

    return unique;
#-------------------------------------------------------------------------------------------------------
# Fim das funções necessárias para login and register
#-------------------------------------------------------------------------------------------------------

#sacar as fotos da pasta onde são guardadas pela camara
@app.route('/<path:filename>') #route que possibilita a vizualização da imagens em tamanho grande e com o nome no URL
def image(filename): #função da imagem a ser "sacada " da pasta
    try:
        w = int(request.args['w']) #
        h = int(request.args['h']) #
    except (KeyError, ValueError):
        return send_from_directory('.', filename)

    try:
        im = Image.open(filename)
        im.thumbnail((w, h), Image.ANTIALIAS)
        io = StringIO.StringIO() 
        im.save(io, format='JPEG') #definição do formato da imagem 
        return Response(io.getvalue(), mimetype='image/jpeg')

    except IOError:
        abort(404) #caso existam erros

    return send_from_directory('.', filename)


#route da pagina web que mostra o correio
@app.route('/Correio') #função de renderização das imagens na pagina template Correio
def sMb_Page_2():
    images = []
    for root, dirs, files in os.walk('.'):
        files.sort()
        for filename in [os.path.join(root, name) for name in files]: #ver os ficheiros no caminho das fotos
            if not filename.endswith('.jpg'): #se nao existir fotos na extenção JPG, continua, se não carrega a foto para o Template Correio
                continue
            im = Image.open(filename) #abre a imagem
            w, h = im.size #define tamanhos
            aspect = 1.0*w/h
            print (filename) #print do nome fa foto
            if aspect > 1.0*WIDTH/HEIGHT:
                width = min(w, WIDTH)
                height = width/aspect
            else:
                height = min(h, HEIGHT)
                width = height*aspect
            images.append({
                'width': int(width),
                'height': int(height),
                'src': filename
            })             
    return render_template("Correio.html", **{
        'images': images
    })
	
#route pagina inicial da Web
@app.route('/')
def sMb_Page_1():
    return render_template('sMb_page1.html')

#route da pagina principal depois de ser efetuado o login
@app.route('/pagPrincipal_comLogin', methods=['POST','GET'])
def pagPrincipal_comLogin():
    return render_template('pagPrincipal_comLogin.html')
	
#pagina sobre da Web
@app.route('/Sobre')
def sobrePage():
    return render_template('Sobre.html')

#route da pagina sobre que se encontra depois de efuado o login
@app.route('/SobreLogin')
def sobreLogin():
    return render_template('Sobre_comLogin.html')

#route para a pagina de vizualização dos utilizadores criados em base de dados
@app.route('/VerUtilizadores')
def listarUtilizadores():
   con = sql.connect("static/database.db") #abre conexao com bd
   con.row_factory = sql.Row
   
   cur = con.cursor()
   cur.execute("select * from clientes") #seleciona a tabela clientes e toda a info
   
   rows = cur.fetchall();
   
   return render_template("VerClientes.html",rows = rows) #renderiza a pagina Ver Utilizadores com toda a info da tabela Clientes da bd

#página de login
@app.route('/Login', methods=['GET', 'POST'])
def login(): #função de login
    error = None
    if request.method == 'POST': #se existirem requestes ao webservice 
        mail = request.form['mail'] #campo pmail
        pssw = request.form['pssw'] #campo password
        completion = validate(mail, pssw) #valida a info com a função criada no inicio do script
        
        if completion == False:
            error = 'Credenciais Invalidas. Por favor tente novamente'
        else:
            return redirect(url_for('pagPrincipal_comLogin')) #credenciais cuincidem com a base de daos entao renderiza a pagina principal com login
            
    return render_template('login.html',error=error)

#route para a pagina de adicionar utilizadores
@app.route('/AdicionarUtilizador', methods=['GET', 'POST']) #adiciona cliente e envia para flask
def AdicionarUtilizador(): #função para adicionar utilizadores
    error = None
    if request.method == 'POST': #se forem feitos requestes 
        name = request.form['name'] #campo nome
        mail = request.form['mail'] #campo mail
        pssw = request.form['pssw'] #campo password
        date = request.form['date'] #campo data de registo
        unique = check(name, mail, pssw, date) #faz verificação com a função criada inicialmente

        if unique == True:
            #return render_template('VerClientes.html')
            return redirect(url_for('listarUtilizador')) #tudo corre bem, mostra a pagina que lista os utilizadores
        else:
            error = 'Mail ou password errados. Por Favor tente novamente.'
            
    return render_template('registoDEclientes.html',error=error) #se der erro mostra mensagem de erro 


#route para ver pagina de Correio depois de apagadas as cartas 
@app.route('/Correio', methods=['POST'])
def Apagar(): #função para apagar as cartas 
    if request.method == 'POST': #se forem feitos requestes
        
        try:
            shutil.rmtree('Img/img', ignore_errors=True) #apaga a pasta onde se encontram as fotografias
            error='Fotografias Apagadas'
        except:
            error='Não Existem Fotografias'
          
        
    return render_template('Correio.html', error=error) #se acontecerem erros dá em mensagem

   
#função para validar o apagar utilizador
def val(mail, pssw):
    con = sql.connect('static/database.db') #abre conexao com a bd
    comp = False
    with con:
                cur = con.cursor()                              
                cur.execute("DELETE FROM clientes WHERE mail=? AND pssw=?",(mail,pssw)) #query SLQ para apagar utilizador onde as credenciais estejam corretas
                rows = cur.fetchall()
                for row in rows:
                    dbmail = row[0]
                    dbpssw = row[1]
                    if dbmail==mail:
                        comp=check_pssw(dbpssw, pssw)
    return comp


#route da página de apagar cliente
@app.route('/Apagar', methods=['GET', 'POST'])
def apagar(): #função para apagar utilizador
    error = None
    if request.method == 'POST': #Se forem feitos requestes 
        mail = request.form['mail'] #campo mail
        pssw = request.form['pssw'] #campo password
        comp = val(mail, pssw) #faz validação com função anterior
        
        if comp == False:
            error = 'Apagado com sucesso!'
            print(error)
            return redirect(url_for('listarUtilizadores')) #tudo certo, paga e renderiza a pagina de listar utilizadores
        else:
            error = 'Erro ao apagar, tente de novo! '
            print(error)
            return redirect(url_for('apagar'))

    return render_template('apagar.html',error=error) #erro, mensagem de erro


#=======================================================================================
#inicio de uma API para uma futura app dedicada|nativa para movel
#=======================================================================================
#teste para a app
''' #multiline comment

@app.route('/app/api')
def enviaApp():
    images = []
    for root, dirs, files in os.walk('.'):
        files.sort()
        for filename in [os.path.join(root, name) for name in files]:
            if not filename.endswith('.jpg'):
                continue
            im = Image.open(filename)
            w, h = im.size
            aspect = 1.0*w/h
            print (filename)
            if aspect > 1.0*WIDTH/HEIGHT:
                width = min(w, WIDTH)
                height = width/aspect
            else:
                height = min(h, HEIGHT)
                width = height*aspect
            images.append({
                'width': int(width),
                'height': int(height),
                'src': filename
            })
            
    return render_template(Correio.html,  **{
          'images': images
    })
'''	
#===========================================================================================

#definição do nosso server 
if __name__ == '__main__':
    app.run(host=HOST, port=PORTA)