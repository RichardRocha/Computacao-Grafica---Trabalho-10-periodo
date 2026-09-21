# Simulação Orbital 3D - View Frustum Culling em ModernGL

Este repositório contém a implementação prática de uma simulação orbital em tempo real desenvolvida em **Python**, **ModernGL** e **GLFW**. O projeto foi concebido como um *stress test* para avaliar os ganhos de desempenho da técnica de **View Frustum Culling** aplicada a uma megastrutura espacial modular.

## 🚀 Funcionalidades

- **Algoritmo de View Frustum Culling:** Extração matemática dos 6 planos da pirâmide de visão e teste de intersecção contra AABB (*Axis-Aligned Bounding Boxes*).
- **Cena de Elevada Densidade:** Matriz 3D composta por 972 módulos espaciais conectados com fuselagem e painéis solares.
- **Renderização Avançada:** Iluminação Blinn-Phong com suporte a múltiplos materiais, planeta Terra procedural com atmosfera e campo de estrelas.
- **Métricas em Tempo Real:** Monitorização contínua de FPS, contagem de objetos visíveis e número de polígonos processados pela GPU.

## 🛠️ Requisitos e Instalação

Garante que tens o Python 3.9+ instalado e executa o comando para instalar as dependências:

```bash
pip install glfw moderngl numpy pyrr