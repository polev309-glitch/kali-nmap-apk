package com.kalihunter

import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import java.util.concurrent.Executors

class MainActivity : AppCompatActivity() {

    private lateinit var targetInput: EditText
    private lateinit var resultText: TextView
    private val executor = Executors.newSingleThreadExecutor()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        targetInput = findViewById(R.id.targetInput)
        resultText = findViewById(R.id.resultText)
        val buttonsLayout = findViewById<LinearLayout>(R.id.buttonsLayout)

        val modes = listOf(
            "Быстрое сканирование" to listOf(21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3306, 3389, 8080, 8443),
            "Все частые порты" to listOf(20, 21, 22, 23, 25, 53, 67, 68, 69, 80, 110, 123, 143, 161, 389, 443, 445, 465, 514, 587, 636, 993, 995, 1080, 1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017),
            "Веб-порты" to listOf(80, 443, 8080, 8443, 8000, 8888, 3000, 5000),
            "Базы данных" to listOf(1433, 1521, 3306, 5432, 6379, 27017, 9200),
            "SSH / FTP / Telnet" to listOf(21, 22, 23, 2222)
        )

        for ((name, ports) in modes) {
            val btn = Button(this).apply {
                text = name
                textSize = 16f
                setTextColor(ContextCompat.getColor(context, R.color.white))
                background = ContextCompat.getDrawable(context, R.drawable.button_bg)
                setPadding(24, 24, 24, 24)
                layoutParams = LinearLayout.LayoutParams(
                    LinearLayout.LayoutParams.MATCH_PARENT,
                    LinearLayout.LayoutParams.WRAP_CONTENT
                ).apply { setMargins(0, 8, 0, 8) }
                setOnClickListener { startScan(ports) }
            }
            buttonsLayout.addView(btn)
        }

        val termuxBtn = Button(this).apply {
            text = "Открыть nmap в Termux"
            textSize = 16f
            setTextColor(ContextCompat.getColor(context, R.color.white))
            background = ContextCompat.getDrawable(context, R.drawable.button_bg)
            setPadding(24, 24, 24, 24)
            layoutParams = LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
            ).apply { setMargins(0, 24, 0, 8) }
            setOnClickListener { openTermux() }
        }
        buttonsLayout.addView(termuxBtn)
    }

    private fun startScan(ports: List<Int>) {
        val target = targetInput.text.toString().trim()
        if (target.isEmpty()) {
            resultText.text = "Введи цель"
            return
        }
        resultText.text = "Сканирую $target..."
        executor.execute {
            val resolved = PortScanner.resolve(target)
            val result = PortScanner.scan(resolved, ports)
            runOnUiThread { resultText.text = result }
        }
    }

    private fun openTermux() {
        val target = targetInput.text.toString().trim()
        if (target.isEmpty()) {
            resultText.text = "Введи цель"
            return
        }
        try {
            val intent = Intent().apply {
                setClassName("com.termux", "com.termux.app.RunCommandService")
                action = "com.termux.RUN_COMMAND"
                putExtra("com.termux.RUN_COMMAND_PATH", "/data/data/com.termux/files/usr/bin/nmap")
                putExtra("com.termux.RUN_COMMAND_ARGUMENTS", arrayOf("-F", "-T4", target))
                putExtra("com.termux.RUN_COMMAND_BACKGROUND", false)
                putExtra("com.termux.RUN_COMMAND_SESSION_ACTION", "0")
            }
            ContextCompat.startForegroundService(this, intent)
            resultText.text = "nmap запущен в Termux для $target"
        } catch (e: Exception) {
            resultText.text = "Ошибка: ${e.message}\n\nTermux не установлен."
        }
    }

    override fun onDestroy() {
        super.onDestroy()
        executor.shutdown()
    }
}
