package com.kalihunter

import java.net.InetSocketAddress
import java.net.Socket

object PortScanner {

    fun scan(host: String, ports: List<Int>, timeoutMs: Int = 500): String {
        val openPorts = mutableListOf<Int>()
        val sb = StringBuilder()

        sb.append("Сканирую $host...\n")
        sb.append("Портов: ${ports.size}\n\n")

        for (port in ports) {
            try {
                val socket = Socket()
                socket.connect(InetSocketAddress(host, port), timeoutMs)
                socket.close()
                openPorts.add(port)
                sb.append("Порт $port: ОТКРЫТ\n")
            } catch (e: Exception) {
                // порт закрыт или таймаут
            }
        }

        if (openPorts.isEmpty()) {
            sb.append("\nОткрытых портов не найдено")
        } else {
            sb.append("\nНайдено открытых портов: ${openPorts.size}")
        }

        return sb.toString()
    }

    fun resolve(host: String): String {
        return try {
            val addr = java.net.InetAddress.getByName(host)
            addr.hostAddress ?: host
        } catch (e: Exception) {
            host
        }
    }
}
