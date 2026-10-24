"""Interfaz de escritorio para el programa de subastas existente."""
import os
import queue
import re
import socket
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, scrolledtext, ttk

from subastas import GRUPO, centavos, ip_local


class Aplicacion:
    def __init__(self, root):
        self.root = root
        self.proceso = None
        self.cola = queue.Queue()
        self.cerrando = False
        root.title('APEB1 · Subastas en vivo')
        root.geometry('940x760')
        root.minsize(800, 690)
        root.configure(bg='#eef2f7')
        estilo = ttk.Style()
        estilo.theme_use('clam')
        estilo.configure('TFrame', background='#eef2f7')
        estilo.configure('TLabel', background='#eef2f7', foreground='#182840', font=('Segoe UI', 10))
        estilo.configure('TButton', font=('Segoe UI', 10), padding=8)
        estilo.configure('Titulo.TLabel', font=('Segoe UI', 24, 'bold'))
        estilo.configure('Precio.TLabel', font=('Segoe UI', 40, 'bold'), foreground='#1565c0')
        base = ttk.Frame(root, padding=24)
        base.pack(fill='both', expand=True)
        ttk.Label(base, text='Subastas en vivo', style='Titulo.TLabel').pack(anchor='w')
        ttk.Label(base, text='APEB1 · Sistemas Distribuidos · Panel de participación').pack(anchor='w', pady=(0, 15))

        config = ttk.Frame(base)
        config.pack(fill='x')
        self.valores = {}
        campos = [('rol', 'Modo', 'Cliente'), ('nombre', 'Nombre del participante', 'Santiago'),
                  ('interfaz', 'IP de este equipo', ip_local()), ('servidor', 'IP del subastador', ip_local()),
                  ('grupo', 'Grupo multicast', GRUPO), ('articulo', 'Artículo (subastador)', 'Computadora portátil'),
                  ('precio', 'Precio inicial ($)', '100.00')]
        self.entradas = []
        for indice, (clave, titulo, defecto) in enumerate(campos):
            fila, columna = divmod(indice, 2)
            celda = ttk.Frame(config, padding=(0, 0, 18, 8))
            celda.grid(row=fila, column=columna, sticky='ew')
            config.columnconfigure(columna, weight=1)
            ttk.Label(celda, text=titulo).pack(anchor='w')
            variable = tk.StringVar(value=defecto)
            self.valores[clave] = variable
            if clave == 'rol':
                campo = ttk.Combobox(celda, textvariable=variable, values=['Cliente', 'Subastador'], state='readonly')
            else:
                campo = ttk.Entry(celda, textvariable=variable)
            campo.pack(fill='x', pady=(3, 0))
            self.entradas.append((clave, campo))

        barra = ttk.Frame(base)
        barra.pack(fill='x', pady=5)
        self.inicio = ttk.Button(barra, text='Iniciar / conectar', command=self.iniciar)
        self.inicio.pack(side='left')
        self.consulta = ttk.Button(barra, text='Consultar estado', command=lambda: self.enviar('estado'), state='disabled')
        self.consulta.pack(side='left', padx=8)
        self.cierre = ttk.Button(barra, text='Cerrar subasta', command=self.cerrar_subasta, state='disabled')
        self.cierre.pack(side='left')
        self.detener = ttk.Button(barra, text='Desconectar', command=self.parar, state='disabled')
        self.detener.pack(side='right')

        self.estado = tk.StringVar(value='SIN CONEXIÓN')
        self.articulo = tk.StringVar(value='Esperando una subasta')
        self.precio = tk.StringVar(value='$ —')
        self.lider = tk.StringVar(value='Líder: —')
        ttk.Separator(base).pack(fill='x', pady=12)
        ttk.Label(base, textvariable=self.estado).pack(anchor='w')
        ttk.Label(base, textvariable=self.articulo, font=('Segoe UI', 14, 'bold')).pack(anchor='w', pady=(5, 0))
        ttk.Label(base, textvariable=self.precio, style='Precio.TLabel').pack(anchor='w')
        ttk.Label(base, textvariable=self.lider).pack(anchor='w')
        puja = ttk.Frame(base)
        puja.pack(fill='x', pady=12)
        ttk.Label(puja, text='Tu oferta ($)').pack(side='left', padx=(0, 10))
        self.monto = ttk.Entry(puja, width=18)
        self.monto.pack(side='left')
        self.monto.bind('<Return>', lambda evento: self.pujar())
        self.boton_puja = ttk.Button(puja, text='Enviar puja', command=self.pujar, state='disabled')
        self.boton_puja.pack(side='left', padx=8)
        ttk.Label(base, text='Historial de actividad').pack(anchor='w')
        self.historial = scrolledtext.ScrolledText(base, height=9, wrap='word', font=('Consolas', 10),
                                                bg='#142238', fg='#e2eaf4', state='disabled')
        self.historial.pack(fill='both', expand=True, pady=(5, 0))
        root.protocol('WM_DELETE_WINDOW', self.salir)
        root.after(100, self.revisar)

    def registrar(self, texto):
        self.historial.configure(state='normal')
        self.historial.insert('end', f'{datetime.now():%H:%M:%S}  {texto}\n')
        self.historial.see('end')
        self.historial.configure(state='disabled')

    def iniciar(self):
        valores = {k: v.get().strip() for k, v in self.valores.items()}
        try:
            if not valores['nombre']:
                raise ValueError('Escriba el nombre del participante.')
            for clave in ['interfaz', 'servidor', 'grupo']:
                socket.inet_pton(socket.AF_INET, valores[clave])
            if not 224 <= int(valores['grupo'].split('.')[0]) <= 239:
                raise ValueError('La dirección del grupo debe ser multicast.')
            centavos(valores['precio'])
        except (OSError, ValueError) as exc:
            messagebox.showerror('Revise la configuración', str(exc))
            return
        self.rol = valores['rol']
        comando = [sys.executable, '-u', str(Path(__file__).with_name('subastas.py')),
                   'cliente' if self.rol == 'Cliente' else 'subastador',
                   '--interfaz', valores['interfaz'], '--servidor', valores['servidor'],
                   '--grupo', valores['grupo'], '--nombre', valores['nombre'],
                   '--articulo', valores['articulo'], '--precio', valores['precio']]
        entorno = dict(os.environ, PYTHONIOENCODING='utf-8')
        try:
            self.proceso = subprocess.Popen(comando, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.STDOUT, text=True, encoding='utf-8',
                                           env=entorno, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        except OSError as exc:
            messagebox.showerror('No se pudo iniciar', str(exc))
            return
        proceso = self.proceso
        def leer():
            for linea in proceso.stdout:
                self.cola.put(('texto', linea.strip()))
            proceso.wait()
            self.cola.put(('fin', proceso.returncode))
        threading.Thread(target=leer, daemon=True).start()
        for _, campo in self.entradas:
            campo.configure(state='disabled')
        self.inicio.configure(state='disabled')
        self.detener.configure(state='normal')
        self.estado.set('INICIANDO…')
        self.precio.set('$ —')
        self.articulo.set('Esperando el estado del subastador')
        self.lider.set('Líder: —')
        self.registrar('Iniciando ' + self.rol.lower())

    def enviar(self, texto):
        if self.proceso and self.proceso.poll() is None:
            try:
                self.proceso.stdin.write(texto + '\n')
                self.proceso.stdin.flush()
                self.registrar('Enviado: ' + texto)
            except (OSError, ValueError):
                self.registrar('No se pudo enviar: conexión finalizada.')

    def pujar(self):
        if self.boton_puja['state'] == 'disabled':
            return
        try:
            centavos(self.monto.get().strip())
        except ValueError as exc:
            messagebox.showerror('Revise su oferta', str(exc))
            return
        self.enviar(self.monto.get().strip())
        self.monto.delete(0, 'end')

    def cerrar_subasta(self):
        self.enviar('cerrar')

    def parar(self):
        self.enviar('salir')
        self.detener.configure(state='disabled')

    def revisar(self):
        while not self.cola.empty():
            tipo, dato = self.cola.get()
            if tipo == 'fin':
                self.registrar(f'Proceso finalizado (código {dato}).')
                self.estado.set('DESCONECTADO')
                self.proceso = None
                for clave, campo in self.entradas:
                    campo.configure(state='readonly' if clave == 'rol' else 'normal')
                self.inicio.configure(state='normal')
                for boton in [self.consulta, self.cierre, self.detener, self.boton_puja]:
                    boton.configure(state='disabled')
                if self.cerrando:
                    self.root.destroy()
                    return
            elif dato:
                texto = dato.replace('cliente> ', '').replace('subastador> ', '').strip()
                if not texto:
                    continue
                self.registrar(texto)
                if 'Subastador en ' in texto:
                    self.estado.set('SUBASTADOR ACTIVO')
                    self.consulta.configure(state='normal')
                    self.cierre.configure(state='normal')
                    self.enviar('estado')
                patron = r'\[(?:ESTADO|ACTUALIZACION|RESULTADO_PUJA|CIERRE)\] (.*?) \| \$(\d+\.\d{2}) \| Líder: (.*?) \| (ABIERTA|CERRADA) \| v(\d+)'
                resultado = re.search(patron, texto)
                if resultado:
                    articulo, precio, lider, estado, version = resultado.groups()
                    self.articulo.set(articulo)
                    self.precio.set('$ ' + precio)
                    self.lider.set('Líder: ' + lider)
                    self.estado.set(f'{estado} · versión {version}')
                    self.consulta.configure(state='normal')
                    self.boton_puja.configure(state='normal' if self.rol == 'Cliente' and estado == 'ABIERTA' else 'disabled')
                    self.cierre.configure(state='normal' if self.rol == 'Subastador' and estado == 'ABIERTA' else 'disabled')
                if 'Se desconectó el subastador' in texto:
                    self.estado.set('CONEXIÓN PERDIDA · desconecte y vuelva a conectar')
                    self.boton_puja.configure(state='disabled')
                    self.consulta.configure(state='disabled')
        self.root.after(100, self.revisar)

    def salir(self):
        if self.proceso and self.proceso.poll() is None:
            self.cerrando = True
            self.parar()
        else:
            self.root.destroy()


if __name__ == '__main__':
    ventana = tk.Tk()
    Aplicacion(ventana)
    ventana.mainloop()
