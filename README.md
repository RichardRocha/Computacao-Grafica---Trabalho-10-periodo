# Simulação Orbital 3D — View Frustum Culling com ModernGL

> **Projeto Científico — Computação Gráfica e Visualização Científica (Engenharia de Computação — FHO)**  
> **Eixo Temático 2:** Engenharia Civil e Modelação CAD (Referência Base: U. Assarsson)  
> **Integrantes:** Richard Nicholas Rocha, Arlyson Silva e Kauan Vitor Torres de Melo

---

## Sobre o Projeto

Este repositório contém a implementação prática e a suíte de avaliação experimental do algoritmo de **View Frustum Culling** aplicado em tempo real a uma megastrutura orbital tridimensional de alta densidade geométrica.

A cena interativa foi desenvolvida em **Python 3.11 / 3.12** utilizando **OpenGL 3.3 Core Profile** (via `ModernGL` e `GLFW`) e é composta por três camadas principais:
* **Megastrutura Orbital Modular:** Grelha 3D contendo **972 módulos interligados** ($420$ triângulos por módulo, totalizando **$408.240$ triângulos**), com corredores de acoplamento nos eixos $X$ e $Z$, fuselagem metálica e painéis solares renderizados com iluminação *Blinn-Phong*.
* **Planeta Terra Procedural:** Esfera tridimensional iluminada por um *fragment shader* procedural com ruído multi-frequência para geração de continentes, oceanos, camadas de nuvens e espalhamento atmosférico (*Atmospheric Rim Glow*).
* **Campo Estelar:** Fundo espacial composto por $3.500$ estrelas renderizadas via primitivas de pontos (`GL_POINTS`).

---

## Fundamentação Matemática

### 1. Extração Analítica dos Planos do Frustum
A cada quadro renderizado, extrai-se diretamente das linhas da matriz transposta combinada $M_{VP} = M_{proj} \times M_{view}$ as equações dos seis planos delimitadores da pirâmide de visão (Esquerdo, Direito, Inferior, Superior, Próximo e Distante), normalizados pela magnitude de seus vetores normais $\mathbf{N} = (A, B, C)$:

$$A x + B y + C z + D = 0$$

### 2. Teste de Intersecção AABB vs. Plano ($p$-positivo)
Cada módulo possui uma caixa delimitadora alinhada aos eixos (*Axis-Aligned Bounding Box* — AABB) definida por $[\mathbf{P}_{min}, \mathbf{P}_{max}]$. Para cada um dos seis planos, determina-se o vértice extremo mais favorável ($\mathbf{p} = (p_x, p_y, p_z)$) na direção do vetor normal:

$$p_x = \begin{cases} x_{max}, & \text{se } A > 0 \\ x_{min}, & \text{se } A \le 0 \end{cases}, \quad
p_y = \begin{cases} y_{max}, & \text{se } B > 0 \\ y_{min}, & \text{se } B \le 0 \end{cases}, \quad
p_z = \begin{cases} z_{max}, & \text{se } C > 0 \\ z_{min}, & \text{se } C \le 0 \end{cases}$$

Caso $A p_x + B p_y + C p_z + D < 0$ para qualquer um dos seis planos, o módulo encontra-se integralmente fora do campo de visão e sua chamada de renderização (*draw call*) é descartada na CPU antes de ser submetida à GPU.

---

## Estrutura do Repositório

```text
Computacao-Grafica---Trabalho-10-periodo/
├── src/
│   ├── main.py                  # Engine gráfica, presets de câmera, benchmark e captura PNG
│   └── plot_results.py          # Script gerador de gráficos (300 DPI) a partir do CSV
├── results/
│   └── benchmark_metrics.csv    # Métricas coletadas automaticamente pela bateria de testes
├── docs/
│   ├── screenshots/             # Capturas de tela do framebuffer OpenGL (PNG)
│   └── charts/                  # Gráficos comparativos de FPS, Frame Time e Descarte
├── requirements.txt             # Dependências do ambiente Python
└── README.md                    # Documentação técnica do projeto
```

---

## Tecnologias e Hardware de Referência

* **Linguagem:** Python 3.11 ou 3.12 (compatibilidade nativa com extensões compiladas do ModernGL)
* **API Gráfica & Janela:** `ModernGL` (OpenGL 3.3 Core Profile) e `GLFW`
* **Cálculo Vetorial & Telemetria:** `NumPy`, `Pyrr`, `psutil` e `Matplotlib`
* **Ambiente de Avaliação:** AMD Ryzen 5 5500, NVIDIA GeForce RTX 4060 (8 GB GDDR6), 16 GB RAM DDR4, resolução $1280 \times 720$.

---

## Instalação e Execução

### 1. Clonar o Repositório
```bash
git clone https://github.com/RichardRocha/Computacao-Grafica---Trabalho-10-periodo.git
cd Computacao-Grafica---Trabalho-10-periodo
```

### 2. Instalar as Dependências
Utilize explicitamente o interpretador **Python 3.11** (ou 3.12) para evitar conflitos de pacotes:
```bash
py -3.11 -m pip install -r requirements.txt
```

### 3. Executar a Simulação Interativa
```bash
py -3.11 src/main.py
```

### 4. Executar o Benchmark Automatizado e Gerar Gráficos
1. Com a janela da simulação aberta, pressione a tecla **`B`** para iniciar a bateria automatizada de 8 testes (alternando *Culling* Desligado e Ligado nos 4 cenários de câmera).
2. Ao final (~20 segundos), os dados serão salvos em `results/benchmark_metrics.csv` e as capturas de tela em `docs/screenshots/`.
3. Gere os gráficos comparativos de desempenho executando:
```bash
py -3.11 src/plot_results.py
```

---

## Controles e Atalhos da Aplicação

| Tecla / Entrada | Ação / Funcionalidade |
| :--- | :--- |
| **`W`, `A`, `S`, `D`** | Movimentação horizontal da câmera (Frente, Esquerda, Trás, Direita) |
| **`Q`, `E`** | Movimentação vertical da câmera (Descer / Subir) |
| **Mouse** | Rotação livre da orientação da câmera ($360^\circ$) |
| **`1`, `2`, `3`, `4`** | Alterna entre os 4 ângulos padronizados de câmera (Frontal, Parcial, Interna, Terra) |
| **`C`** | Liga / Desliga o *View Frustum Culling* em tempo real |
| **`V`** | Liga / Desliga a sincronização vertical (*V-Sync*) |
| **`B`** | Executa o benchmark automatizado e exporta o arquivo CSV de métricas |
| **`F12`** | Salva uma captura de tela PNG na pasta `docs/screenshots/` |
| **`ESC`** | Encerra a aplicação |
