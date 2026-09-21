# 🛰️ Simulação Orbital 3D — View Frustum Culling com ModernGL

> **Projeto Acadêmico / Demonstração Técnica (IEEE Style)**  
> Implementação em tempo real do algoritmo de *View Frustum Culling* aplicado a uma megastrutura orbital de alta densidade geométrica, desenvolvido em Python 3.9+ e OpenGL 3.3 Core via ModernGL.

---

## 📋 Sobre o Projeto

Este projeto consiste numa simulação gráfica tridimensional de um ambiente espacial contendo uma estação orbital modular disposta em uma matriz 3D (composta por **972 módulos interligados**, totalizando mais de **400.000 triângulos**), um planeta Terra procedural com atmosfera e um campo de estrelas.

O objetivo principal é demonstrar na prática os ganhos de desempenho obtidos ao aplicar a técnica de **View Frustum Culling** ($AABB \times 6\text{ Planos do Frustum}$) para descartar dados geométricos fora do campo de visão da câmara antes de enviá-los para a GPU (*draw calls*).

---

## ✨ Recursos Principais

- **Algoritmo de View Frustum Culling:** Extração dinâmica dos 6 planos da pirâmide de visão a partir da matriz $M = M_{proj} \times M_{view}$ e teste de intersecção com caixas delimitadoras (*Axis-Aligned Bounding Boxes* - AABB).
- **Grelha 3D de Alta Densidade:** Estação espacial composta por 972 módulos com corredores de acoplamento nos eixos $X$ e $Z$, servindo de *stress test* para a pipeline gráfica.
- **Shader Procedural do Planeta Terra:** Renderização procedural baseada em ruído multi-frequência para continentes, oceanos, nuvens e retroiluminação atmosférica (*Atmospheric Rim Glow*).
- **Iluminação Blinn-Phong & Materiais:** Shader de iluminação espacial diferenciando fuselagem metálica (alta reflexão especular) e painéis solares de silício.
- **Métricas e Telemetria em Tempo Real:** Exibição no terminal de FPS, contagem de objetos visíveis e número de polígonos ativos na GPU.
- **Alternância Dinâmica:** Ativação e desativação do *culling* em tempo real pressionando a tecla `C`.

---

## 📐 Fundamentação Matemática

### 1. Extração dos Planos da Pirâmide de Visão
A partir da multiplicação das matrizes de Projeção e Visão $M = M_{proj} \cdot M_{view}$, os 6 planos da pirâmide de visão (Esquerdo, Direito, Inferior, Superior, Próximo e Distante) são extraídos e normalizados segundo a equação geral do plano:

$$A x + B y + C z + D = 0$$

### 2. Teste AABB vs. Plano
Para cada módulo espacial posicionado na matriz 3D, calcula-se a sua caixa delimitadora $AABB = [P_{min}, P_{max}]$. O algoritmo avalia se o ponto extremo mais favorável em relação à normal de cada plano está contido no lado positivo do espaço. Se o objeto estiver totalmente atrás de pelo menos um dos 6 planos, é descartado (*culled*).

$$\text{Ponto Positivo } P_x = \begin{cases} x_{max}, & \text{se } A > 0 \\ x_{min}, & \text{caso contrário} \end{cases}$$

Se $A P_x + B P_y + C P_z + D < 0$, o objeto encontra-se fora do campo de visão.

---

## 🛠️ Tecnologias Utilizadas

- **Linguagem:** Python 3.9+
- **API Gráfica:** OpenGL 3.3 Core via [ModernGL](https://moderngl.readthedocs.io/)
- **Contexto & Janela:** [GLFW](https://www.glfw.org/)
- **Cálculo Vetorial e Matricial:** [NumPy](https://numpy.org/) e [Pyrr](https://pyrr.readthedocs.io/)

---

## 🚀 Instalação e Execução

### Pré-requisitos
Garantir que o Python 3.9 (ou superior) está instalado no sistema.

### 1. Clonar o Repositório
```bash
git clone https://github.com/RichardRocha/Computacao-Grafica---Trabalho-10-periodo.git
cd Computacao-Grafica---Trabalho-10-periodo

### 2. Instalar Dependências
```bash
pip install moderngl glfw numpy pyrr

### 3. Executar a Simulação
```bash
python main.py

### 🎮 Comandos e Controles
Tecla / Ação	Função
W, A, S, D	Movimentação da câmara (Frente, Esquerda, Trás, Direita)
Q, E	Movimento vertical (Descendo, Subindo)
Rato (Mouse)	Orientação e rotação da câmara em 360°
Tecla C	Alterna entre View Frustum Culling (LIGADO / DESLIGADO)
Tecla ESC	Encerra a simulação