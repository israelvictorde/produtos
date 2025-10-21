-- Criar banco de dados
CREATE DATABASE IF NOT EXISTS app_produtos;
USE app_produtos;

-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Tabela de produtos
CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10,2),
    category VARCHAR(50),
    quantity INT DEFAULT 0,
    is_available BOOLEAN DEFAULT TRUE,
    user_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Tabela de categorias (opcional)
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Inserir categorias padrão
INSERT IGNORE INTO categories (name, description) VALUES
('Eletrônicos', 'Produtos eletrônicos em geral'),
('Roupas', 'Vestuário e acessórios'),
('Livros', 'Livros e materiais de leitura'),
('Casa', 'Produtos para casa'),
('Esportes', 'Artigos esportivos'),
('Outros', 'Outras categorias');

-- Inserir usuário admin padrão
-- Inserir apenas o admin (com IGNORE para evitar duplicatas)
INSERT IGNORE INTO users (username, email, password, full_name) 
VALUES ('admin', 'admin@app.com', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj89tiM7FEVK', 'Administrador');

-- Para usuários adicionais, usar INSERT normal ou procedimento separado
INSERT INTO users (username, email, password, full_name) 
VALUES ('novousuario', 'novo@email.com', '$2b$12$hashedpassword', 'Novo Usuário');

-- Inserir alguns produtos de exemplo
INSERT IGNORE INTO products (name, description, price, category, quantity, user_id) VALUES
('Smartphone XYZ', 'Smartphone com 128GB, câmera tripla', 899.99, 'Eletrônicos', 10, 1),
('Livro Python', 'Aprenda Python do zero ao avançado', 49.90, 'Livros', 25, 1),
('Camiseta Básica', 'Camiseta 100% algodão, várias cores', 29.90, 'Roupas', 50, 2);