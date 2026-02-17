// OnTime - JavaScript Principal

/**
 * Formata um número como tempo (HH:MM)
 */
function formatarTempo(horas) {
    const h = Math.floor(Math.abs(horas));
    const m = Math.round((Math.abs(horas) - h) * 60);
    const sinal = horas < 0 ? '-' : '';
    return `${sinal}${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
}

/**
 * Confirma ação antes de executar
 */
function confirmarAcao(mensagem) {
    return confirm(mensagem || 'Tem certeza que deseja realizar esta ação?');
}

/**
 * Copia texto para área de transferência
 */
async function copiarTexto(texto) {
    try {
        await navigator.clipboard.writeText(texto);
        alert('Texto copiado!');
    } catch (err) {
        console.error('Erro ao copiar texto:', err);
    }
}

/**
 * Formata data para exibição
 */
function formatarData(data) {
    const d = new Date(data);
    const dia = String(d.getDate()).padStart(2, '0');
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const ano = d.getFullYear();
    return `${dia}/${mes}/${ano}`;
}

/**
 * Auto-dismiss de mensagens após 5 segundos
 */
document.addEventListener('DOMContentLoaded', function() {
    const messages = document.querySelectorAll('[role="alert"]');
    messages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 5000);
    });
});

/**
 * Confirmação antes de enviar formulários críticos
 */
document.addEventListener('DOMContentLoaded', function() {
    const formsComConfirmacao = document.querySelectorAll('[data-confirmar]');
    formsComConfirmacao.forEach(function(form) {
        form.addEventListener('submit', function(e) {
            const mensagem = form.dataset.confirmar;
            if (!confirmarAcao(mensagem)) {
                e.preventDefault();
            }
        });
    });
});

/**
 * Loading state em botões de submit
 */
document.addEventListener('DOMContentLoaded', function() {
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                submitBtn.classList.add('opacity-50', 'cursor-not-allowed');
                const originalText = submitBtn.textContent;
                submitBtn.textContent = 'Processando...';
                
                // Restaurar após 10 segundos (fallback)
                setTimeout(function() {
                    submitBtn.disabled = false;
                    submitBtn.classList.remove('opacity-50', 'cursor-not-allowed');
                    submitBtn.textContent = originalText;
                }, 10000);
            }
        });
    });
});