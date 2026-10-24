"""Pruebas locales reproducibles; no sustituyen las pruebas en red virtual."""
import concurrent.futures
import json
import socket
import unittest
from subastas import Subasta, centavos, emisor, receptor, ip_local


class Pruebas(unittest.TestCase):
    def test_montos(self):
        self.assertEqual(centavos('110.50'), 11050)
        for valor in ['NaN', 'Infinity', '-1', '0', '1.001', 'abc']:
            with self.assertRaises(ValueError):
                centavos(valor)

    def test_concurrencia_y_cierre(self):
        subasta = Subasta('Artículo', 10000)
        montos = list(range(10100, 20100, 100))
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as pool:
            resultados = list(pool.map(lambda monto: subasta.pujar(str(monto), str(monto), monto), montos))
        self.assertEqual(subasta.estado()['precio'], max(montos))
        self.assertEqual(subasta.estado()['version'], sum(r['aceptada'] for r in resultados))
        self.assertFalse(subasta.pujar('Otro', 'empate', max(montos))['aceptada'])
        subasta.cerrar()
        self.assertFalse(subasta.pujar('Otro', 'cerrada', 999999)['aceptada'])

    def test_oferta_repetida(self):
        subasta = Subasta('Artículo', 10000)
        primero = subasta.pujar('Cliente', 'id-1', 11000)
        self.assertEqual(primero, subasta.pujar('Cliente', 'id-1', 12000))
        self.assertEqual(subasta.estado()['precio'], 11000)
        self.assertEqual(subasta.estado()['version'], 1)

    def test_multicast_dos_receptores(self):
        puerto = 15001
        with receptor(ip_local(), puerto=puerto) as uno, receptor(ip_local(), puerto=puerto) as dos, emisor(ip_local()) as origen:
            uno.settimeout(3)
            dos.settimeout(3)
            mensaje = dict(tipo='ACTUALIZACION', precio=12000, version=1)
            origen.sendto(json.dumps(mensaje).encode(), ('239.255.42.99', puerto))
            self.assertEqual(json.loads(uno.recvfrom(65535)[0]), mensaje)
            self.assertEqual(json.loads(dos.recvfrom(65535)[0]), mensaje)


if __name__ == '__main__':
    unittest.main(verbosity=2)
