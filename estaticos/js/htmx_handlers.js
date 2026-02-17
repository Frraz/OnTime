// OnTime - Handlers HTMX

/**
 * Configuração global do HTMX
 */
document.addEventListener('DOMContentLoaded', function() {
    // Indicador de loading global
    document.body.addEventListener('htmx:beforeRequest', function(event) {
        const target = event.detail.target;
        if (target) {
            target.classList.add('htmx-loading');
        }
    });
    
    document.body.addEventListener('htmx:afterRequest', function(event) {
        const target = event.detail.target;
        if (target) {
            target.classList.remove('htmx-loading');
        }
    });
    
    // Erro de requisição
    document.body.addEventListener('htmx:responseError', function(event) {
        console.error('Erro HTMX:', event.detail);
        alert('Erro ao processar requisição. Tente novamente.');
    });
    
    // Timeout de requisição
    document.body.addEventListener('htmx:timeout', function(event) {
        console.error('Timeout HTMX:', event.detail);
        alert('A requisição demorou muito. Tente novamente.');
    });
});

/**
 * Atualização automática de elementos
 */
function iniciarAtualizacaoAutomatica(seletor, intervalo) {
    const elementos = document.querySelectorAll(seletor);
    elementos.forEach(function(elemento) {
        setInterval(function() {
            htmx.trigger(elemento, 'refresh');
        }, intervalo);
    });
}