from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'sua_chave_secreta_aqui'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///produtos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Modelos (mantenha os mesmos)
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    products = db.relationship('Product', backref='owner', lazy=True)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=True)
    category = db.Column(db.String(50))
    quantity = db.Column(db.Integer, default=0)
    is_available = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Função para inicializar o banco de dados
def init_db():
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        
        # Verificar se já existem categorias para evitar duplicatas
        if Category.query.count() == 0:
            default_categories = [
                ('Eletrônicos', 'Produtos eletrônicos em geral'),
                ('Roupas', 'Vestuário e acessórios'),
                ('Livros', 'Livros e materiais de leitura'),
                ('Casa', 'Produtos para casa'),
                ('Esportes', 'Artigos esportivos'),
                ('Outros', 'Outras categorias')
            ]
            
            for cat_name, cat_desc in default_categories:
                category = Category(name=cat_name, description=cat_desc)
                db.session.add(category)
        
        # Verificar se usuário admin já existe
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@app.com',
                password=generate_password_hash('admin123'),
                full_name='Administrador'
            )
            db.session.add(admin_user)
        
        # Verificar se usuário de teste já existe
        if not User.query.filter_by(username='usuario1').first():
            test_user = User(
                username='usuario1',
                email='usuario1@email.com',
                password=generate_password_hash('senha123'),
                full_name='Usuário Teste 1'
            )
            db.session.add(test_user)
        
        # Verificar se já existem produtos
        if Product.query.count() == 0:
            sample_products = [
                ('Smartphone XYZ', 'Smartphone com 128GB, câmera tripla', 899.99, 'Eletrônicos', 10, 1),
                ('Livro Python', 'Aprenda Python do zero ao avançado', 49.90, 'Livros', 25, 1),
                ('Camiseta Básica', 'Camiseta 100% algodão, várias cores', 29.90, 'Roupas', 50, 2)
            ]
            
            for name, description, price, category, quantity, user_id in sample_products:
                # Encontrar o ID do usuário correto
                user = User.query.get(user_id)
                if user:
                    product = Product(
                        name=name,
                        description=description,
                        price=price,
                        category=category,
                        quantity=quantity,
                        user_id=user.id
                    )
                    db.session.add(product)
        
        try:
            db.session.commit()
            print("Banco de dados inicializado com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao inicializar banco: {e}")

# Middleware para verificar autenticação
@app.before_request
def require_login():
    allowed_routes = ['login', 'register', 'static', 'index', 'init_database']
    if request.endpoint not in allowed_routes and 'user_id' not in session:
        return redirect(url_for('login'))

# Rota para inicializar o banco de dados
@app.route('/init-db')
def init_database():
    init_db()
    flash('Banco de dados inicializado com sucesso!', 'success')
    return redirect(url_for('login'))

# Rotas de Autenticação
@app.route('/')
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username, is_active=True).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['full_name'] = user.full_name
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha incorretos!', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        full_name = request.form['full_name']
        
        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe!', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado!', 'error')
            return render_template('register.html')
        
        # Criar novo usuário
        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password),
            full_name=full_name
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Conta criada com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar conta!', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

# Rotas Principais
@app.route('/dashboard')
def dashboard():
    user_products_count = Product.query.filter_by(user_id=session['user_id']).count()
    total_products_count = Product.query.count()
    total_users_count = User.query.filter_by(is_active=True).count()
    
    return render_template('dashboard.html',
                         user_products_count=user_products_count,
                         total_products_count=total_products_count,
                         total_users_count=total_users_count)

@app.route('/products')
def products():
    user_products = Product.query.filter_by(user_id=session['user_id']).all()
    categories = Category.query.all()
    return render_template('products.html', products=user_products, categories=categories)

@app.route('/users')
def users():
    if session.get('username') != 'admin':
        flash('Acesso restrito para administradores!', 'error')
        return redirect(url_for('dashboard'))
    
    all_users = User.query.all()
    return render_template('users.html', users=all_users)

# API Routes - CORRIGIDAS COM DEBUG
@app.route('/api/products', methods=['GET', 'POST'])
def api_products():
    if request.method == 'GET':
        products = Product.query.filter_by(user_id=session['user_id']).all()
        products_list = []
        for product in products:
            products_list.append({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'category': product.category,
                'quantity': product.quantity,
                'is_available': product.is_available,
                'created_at': product.created_at.strftime('%d/%m/%Y %H:%M')
            })
        return jsonify(products_list)
    
    elif request.method == 'POST':
        try:
            print(f"Content-Type: {request.content_type}")
            print(f"Headers: {dict(request.headers)}")
            
            # Tenta obter dados como JSON primeiro
            if request.is_json:
                data = request.get_json()
                print(f"Dados JSON: {data}")
            else:
                # Se não for JSON, tenta form data
                data = request.form.to_dict()
                print(f"Dados Form: {data}")
            
            # Validar campos obrigatórios
            if not data.get('name'):
                return jsonify({'error': 'Nome é obrigatório'}), 400
            if not data.get('description'):
                return jsonify({'error': 'Descrição é obrigatória'}), 400
            
            new_product = Product(
                name=data['name'],
                description=data['description'],
                price=float(data['price']) if data.get('price') else None,
                category=data.get('category', 'Outros'),
                quantity=int(data['quantity']) if data.get('quantity') else 0,
                user_id=session['user_id']
            )
            
            db.session.add(new_product)
            db.session.commit()
            
            return jsonify({
                'message': 'Produto cadastrado com sucesso!',
                'product': {
                    'id': new_product.id,
                    'name': new_product.name,
                    'description': new_product.description,
                    'price': new_product.price,
                    'category': new_product.category,
                    'quantity': new_product.quantity,
                    'created_at': new_product.created_at.strftime('%d/%m/%Y %H:%M')
                }
            }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"Erro completo: {str(e)}")
            return jsonify({'error': f'Erro interno: {str(e)}'}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT', 'DELETE'])
def product_detail(product_id):
    product = Product.query.filter_by(id=product_id, user_id=session['user_id']).first()
    
    if not product:
        return jsonify({'error': 'Produto não encontrado'}), 404
    
    if request.method == 'PUT':
        try:
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form.to_dict()
            
            if 'name' in data:
                product.name = data['name']
            if 'description' in data:
                product.description = data['description']
            if 'price' in data:
                product.price = float(data['price']) if data['price'] else None
            if 'category' in data:
                product.category = data['category']
            if 'quantity' in data:
                product.quantity = int(data['quantity']) if data['quantity'] else 0
            if 'is_available' in data:
                product.is_available = bool(data['is_available'])
            
            db.session.commit()
            
            return jsonify({'message': 'Produto atualizado com sucesso!'})
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Erro ao atualizar: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(product)
            db.session.commit()
            return jsonify({'message': 'Produto deletado com sucesso!'})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': f'Erro ao deletar: {str(e)}'}), 500

@app.route('/api/users', methods=['GET', 'POST'])
def api_users():
    # Verificar se é admin
    if session.get('username') != 'admin':
        return jsonify({'error': 'Acesso não autorizado'}), 403
    
    if request.method == 'GET':
        users = User.query.all()
        users_list = []
        for user in users:
            users_list.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'is_active': user.is_active,
                'created_at': user.created_at.strftime('%d/%m/%Y'),
                'products_count': len(user.products)
            })
        return jsonify(users_list)
    
    elif request.method == 'POST':
        try:
            print(f"=== DEBUG API USERS ===")
            print(f"Content-Type: {request.content_type}")
            print(f"Method: {request.method}")
            print(f"Form data: {request.form}")
            
            # Para formulários HTML, usa request.form
            if request.content_type and 'application/x-www-form-urlencoded' in request.content_type:
                data = {
                    'username': request.form.get('username'),
                    'email': request.form.get('email'), 
                    'password': request.form.get('password'),
                    'full_name': request.form.get('full_name')
                }
            elif request.content_type and 'multipart/form-data' in request.content_type:
                data = {
                    'username': request.form.get('username'),
                    'email': request.form.get('email'),
                    'password': request.form.get('password'), 
                    'full_name': request.form.get('full_name')
                }
            elif request.is_json:
                data = request.get_json()
            else:
                # Fallback: tenta form primeiro, depois JSON
                data = request.form.to_dict()
                if not data:
                    data = request.get_json(force=True, silent=True) or {}
            
            print(f"Dados processados: {data}")
            
            # Validar campos obrigatórios
            required_fields = ['username', 'email', 'password', 'full_name']
            missing_fields = []
            
            for field in required_fields:
                if not data.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                error_msg = f'Campos obrigatórios faltando: {", ".join(missing_fields)}'
                print(f"ERRO: {error_msg}")
                return jsonify({'error': error_msg}), 400
            
            # Verificar se usuário já existe
            if User.query.filter_by(username=data['username']).first():
                print(f"ERRO: Usuário {data['username']} já existe")
                return jsonify({'error': 'Nome de usuário já existe'}), 400
            
            if User.query.filter_by(email=data['email']).first():
                print(f"ERRO: Email {data['email']} já existe")
                return jsonify({'error': 'Email já cadastrado'}), 400
            
            # Criar novo usuário
            new_user = User(
                username=data['username'],
                email=data['email'],
                password=generate_password_hash(data['password']),
                full_name=data['full_name']
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            print(f"SUCESSO: Usuário {data['username']} criado")
            
            # Se for requisição de formulário, redireciona com flash message
            if request.content_type and ('application/x-www-form-urlencoded' in request.content_type or 
                                      'multipart/form-data' in request.content_type):
                flash('Usuário criado com sucesso!', 'success')
                return redirect(url_for('users'))
            else:
                # Se for API JSON, retorna JSON response
                return jsonify({
                    'message': 'Usuário criado com sucesso!',
                    'user': {
                        'id': new_user.id,
                        'username': new_user.username,
                        'email': new_user.email,
                        'full_name': new_user.full_name
                    }
                }), 201
            
        except Exception as e:
            db.session.rollback()
            print(f"ERRO INTERNO: {str(e)}")
            import traceback
            print(f"TRACEBACK: {traceback.format_exc()}")
            
            # Se for requisição de formulário, redireciona com erro
            if request.content_type and ('application/x-www-form-urlencoded' in request.content_type or 
                                      'multipart/form-data' in request.content_type):
                flash(f'Erro ao criar usuário: {str(e)}', 'error')
                return redirect(url_for('users'))
            else:
                return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

@app.route('/api/categories', methods=['GET'])
def api_categories():
    categories = Category.query.all()
    categories_list = []
    for category in categories:
        categories_list.append({
            'id': category.id,
            'name': category.name,
            'description': category.description
        })
    return jsonify(categories_list)

if __name__ == '__main__':
    # Inicializar banco de dados automaticamente
    with app.app_context():
        init_db()
    
    app.run(debug=True, port=5000)