"""Subasta educativa: control TCP y anuncios UDP multicast. Python 3.11+."""
import argparse
import json
import socket
import threading
import time
import uuid
from decimal import Decimal, InvalidOperation

GRUPO = '239.255.42.99'
TCP = 5000
UDP = 5001


def ip_local():
    return socket.gethostbyname(socket.gethostname())


def centavos(texto):
    try:
        valor = Decimal(str(texto))
        if not valor.is_finite() or valor <= 0 or valor * 100 != (valor * 100).to_integral_value():
            raise ValueError('Use un monto positivo con hasta dos decimales.')
        return int(valor * 100)
    except InvalidOperation as exc:
        raise ValueError('Monto inválido.') from exc


def enviar(sock, mensaje):
    sock.sendall((json.dumps(mensaje, ensure_ascii=False) + '\n').encode('utf-8'))


class Subasta:
    def __init__(self, articulo, precio):
        self.lock = threading.Lock()
        self.datos = dict(subasta=uuid.uuid4().hex, articulo=articulo,
                          precio=precio, lider=None, abierta=True, version=0)
        self.ofertas = {}

    def estado(self):
        with self.lock:
            return dict(self.datos)

    def pujar(self, participante, oferta, monto):
        with self.lock:
            clave = (participante, oferta)
            if clave in self.ofertas:
                return self.ofertas[clave]
            motivo = None
            if not self.datos['abierta']:
                motivo = 'La subasta está cerrada.'
            elif type(monto) is not int or monto <= 0:
                motivo = 'El monto debe ser un entero positivo en centavos.'
            elif monto <= self.datos['precio']:
                motivo = 'La oferta debe superar el precio actual.'
            if motivo is None:
                self.datos.update(precio=monto, lider=participante,
                                  version=self.datos['version'] + 1)
            resultado = dict(tipo='RESULTADO_PUJA', oferta=oferta,
                             aceptada=motivo is None, motivo=motivo,
                             **self.datos)
            self.ofertas[clave] = resultado
            return resultado

    def cerrar(self):
        with self.lock:
            if self.datos['abierta']:
                self.datos.update(abierta=False, version=self.datos['version'] + 1)


def emisor(ip):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
    return sock


def receptor(ip, grupo=GRUPO, puerto=UDP):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('', puerto))
    membresia = socket.inet_aton(grupo) + socket.inet_aton(ip)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membresia)
    return sock


def servidor(args):
    subasta = Subasta(args.articulo, centavos(args.precio))
    anuncio = emisor(args.interfaz)
    envio_lock = threading.Lock()

    def anunciar():
        with envio_lock:
            estado = subasta.estado()
            mensaje = dict(tipo='ACTUALIZACION' if estado['abierta'] else 'CIERRE', **estado)
            anuncio.sendto(json.dumps(mensaje, ensure_ascii=False).encode('utf-8'),
                           (args.grupo, args.udp))

    def atender(conn, direccion):
        with conn:
            conn.settimeout(300)
            try:
                with conn.makefile('r', encoding='utf-8') as entrada:
                    nombre = None
                    for linea in entrada:
                        if len(linea) > 8192:
                            break
                        mensaje = json.loads(linea)
                        tipo = mensaje.get('tipo')
                        if tipo == 'IDENTIFICACION' and nombre is None:
                            nombre = str(mensaje.get('nombre', '')).strip()[:100]
                            if not nombre:
                                break
                            enviar(conn, dict(tipo='ESTADO', **subasta.estado()))
                            print(f'Conectado: {nombre} desde {direccion[0]}', flush=True)
                        elif tipo == 'ESTADO' and nombre:
                            enviar(conn, dict(tipo='ESTADO', **subasta.estado()))
                        elif tipo == 'PUJA' and nombre:
                            oferta = mensaje.get('oferta')
                            if not isinstance(oferta, str) or not 1 <= len(oferta) <= 100:
                                break
                            resultado = subasta.pujar(nombre, oferta, mensaje.get('monto'))
                            enviar(conn, resultado)
                            if resultado['aceptada']:
                                anunciar()
                        else:
                            enviar(conn, dict(tipo='ERROR', motivo='Mensaje no permitido.'))
            except (OSError, ValueError, AttributeError) as exc:
                print(f'Conexión finalizada {direccion}: {exc}', flush=True)

    escucha = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    escucha.bind((args.interfaz, args.tcp))
    escucha.listen(16)

    def aceptar():
        while True:
            conn, direccion = escucha.accept()
            threading.Thread(target=atender, args=(conn, direccion), daemon=True).start()

    def periodico():
        while True:
            anunciar()
            time.sleep(2)

    threading.Thread(target=aceptar, daemon=True).start()
    threading.Thread(target=periodico, daemon=True).start()
    print(f'Subastador en {args.interfaz}:{args.tcp}; multicast {args.grupo}:{args.udp}')
    print('Comandos: estado | cerrar | salir. Tras cerrar, espere a que los clientes vean el resultado.')
    try:
        while True:
            comando = input('subastador> ').strip().lower()
            if comando == 'cerrar':
                subasta.cerrar()
                anunciar()
                mostrar(dict(tipo='CIERRE', **subasta.estado()))
            elif comando == 'estado':
                mostrar(dict(tipo='ESTADO', **subasta.estado()))
            elif comando == 'salir':
                subasta.cerrar()
                anunciar()
                break
    except (KeyboardInterrupt, EOFError):
        subasta.cerrar()
        anunciar()
    finally:
        escucha.close()
        anuncio.close()


def mostrar(mensaje):
    if 'precio' in mensaje:
        precio = Decimal(mensaje['precio']) / 100
        print(f"\n[{mensaje['tipo']}] {mensaje['articulo']} | ${precio:.2f} | "
              f"Líder: {mensaje['lider'] or 'sin pujas'} | "
              f"{'ABIERTA' if mensaje['abierta'] else 'CERRADA'} | v{mensaje['version']}", flush=True)
    if mensaje.get('tipo') == 'RESULTADO_PUJA':
        print('Oferta aceptada.' if mensaje['aceptada'] else f"Rechazada: {mensaje['motivo']}", flush=True)


def cliente(args):
    multicast = receptor(args.interfaz, args.grupo, args.udp)
    conn = socket.create_connection((args.servidor, args.tcp), timeout=10)
    conn.settimeout(None)
    enviar(conn, dict(tipo='IDENTIFICACION', nombre=args.nombre))
    estado_lock = threading.Lock()
    ultima = {'version': -1, 'subasta': None}

    def actualizar(mensaje, origen):
        with estado_lock:
            version = mensaje.get('version', -1)
            if ultima['subasta'] not in (None, mensaje.get('subasta')):
                return
            if version > ultima['version']:
                if ultima['version'] >= 0 and version > ultima['version'] + 1:
                    print('\nSalto de versiones detectado; se aplica el estado completo recibido.')
                ultima.update(version=version, subasta=mensaje.get('subasta'))
                print(f'\nOrigen: {origen}', flush=True)
                mostrar(mensaje)
            elif mensaje.get('tipo') == 'ESTADO' and version == ultima['version']:
                print(f'\nOrigen: {origen}', flush=True)
                mostrar(mensaje)
            elif mensaje.get('tipo') == 'RESULTADO_PUJA':
                print('\nOferta aceptada.' if mensaje['aceptada'] else f"\nRechazada: {mensaje['motivo']}", flush=True)

    def recibir_tcp():
        try:
            with conn.makefile('r', encoding='utf-8') as entrada:
                for linea in entrada:
                    actualizar(json.loads(linea), 'TCP')
        except (OSError, ValueError):
            pass
        print('\nSe desconectó el subastador. Cierre este cliente y vuelva a conectarse.', flush=True)

    def recibir_multicast():
        while True:
            try:
                datos, direccion = multicast.recvfrom(65535)
                if direccion[0] == args.servidor:
                    actualizar(json.loads(datos), 'MULTICAST')
            except (OSError, ValueError):
                return

    threading.Thread(target=recibir_tcp, daemon=True).start()
    threading.Thread(target=recibir_multicast, daemon=True).start()
    print('Escriba un monto (ej. 110.50), estado o salir.')
    try:
        while True:
            comando = input('cliente> ').strip().lower()
            if not comando:
                continue
            if comando == 'salir':
                break
            if comando == 'estado':
                enviar(conn, dict(tipo='ESTADO'))
            else:
                try:
                    monto = centavos(comando)
                except ValueError as exc:
                    print(exc)
                    continue
                enviar(conn, dict(tipo='PUJA', oferta=uuid.uuid4().hex, monto=monto))
    except (KeyboardInterrupt, EOFError, OSError):
        pass
    finally:
        conn.close()
        multicast.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rol', choices=['subastador', 'cliente'])
    parser.add_argument('--interfaz', default=ip_local(), help='IP local o IP de ZeroTier de este equipo')
    parser.add_argument('--servidor', default=ip_local(), help='IP del subastador')
    parser.add_argument('--nombre', default='Participante')
    parser.add_argument('--articulo', default='Computadora portátil')
    parser.add_argument('--precio', default='100.00')
    parser.add_argument('--grupo', default=GRUPO)
    parser.add_argument('--tcp', type=int, default=TCP)
    parser.add_argument('--udp', type=int, default=UDP)
    args = parser.parse_args()
    try:
        (servidor if args.rol == 'subastador' else cliente)(args)
    except (OSError, ValueError) as exc:
        parser.exit(1, f'No se pudo iniciar: {exc}\n')


if __name__ == '__main__':
    main()
