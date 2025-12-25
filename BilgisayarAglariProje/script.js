document.addEventListener('DOMContentLoaded', () => {
    
    // ----------------------------------------
    // SABİTLER (DOM Elementleri)
    // ----------------------------------------
    const qosForm = document.getElementById('qos-form');
    const calcBtn = document.getElementById('calcBtn');
    const algorithmCards = document.querySelectorAll('.algorithm-card');
    const selectedAlgInput = document.getElementById('selected-algorithm-input');
    const outputAlgDisplay = document.getElementById('output-alg');

    // Sonuç Ekranları
    const totalCostDisplay = document.getElementById('total-cost-display');
    const pathDisplay = document.getElementById('path-display');
    const relVal = document.getElementById('rel-val');
    const delayVal = document.getElementById('delay-val');
    const usageVal = document.getElementById('usage-val');
    const resultDisplay = document.getElementById('result-display');
    const networkGraphImg = document.getElementById('network-graph');
    const graphPlaceholder = document.getElementById('graph-placeholder');
    const metricsBreakdown = document.getElementById('metrics-breakdown'); 

    // YENİ SONUÇ EKLEME: metrics-breakdown'dan sonraki genişletilmiş sonuç alanı
    const extraResultsContainer = document.createElement('div');
    extraResultsContainer.id = 'extra-results-container';
    // Düzeltme: Kenarlık rengi koyu gri yerine açık gri (border-gray-200) olarak ayarlandı
    extraResultsContainer.className = 'mt-4 border-t pt-4 border-gray-200'; 
    
    if (metricsBreakdown) {
        metricsBreakdown.after(extraResultsContainer);
    } else {
        console.error("metrics-breakdown ID'li element bulunamadı. Genişletilmiş sonuçlar eklenemiyor.");
    }

    

    // ----------------------------------------
    // 1. Algoritma Kartı Seçimi Yönetimi
    // ----------------------------------------
    algorithmCards.forEach(card => {
        card.addEventListener('click', () => {
            // Tüm kartlardan 'active' sınıfını kaldır
            algorithmCards.forEach(c => c.classList.remove('active'));
            
            // Tıklanan karta 'active' sınıfını ekle
            card.classList.add('active');
            
            // Gizli input ve sonuç başlığını güncelle
            const selectedAlg = card.getAttribute('data-alg');
            selectedAlgInput.value = selectedAlg;
            outputAlgDisplay.textContent = selectedAlg;
        });
    });

    // ----------------------------------------
    // 2. Form Gönderimi ve API Çağrısı
    // ----------------------------------------
    calcBtn.addEventListener('click', async () => {
        
        // Butonu devre dışı bırak ve yükleniyor animasyonu ekle
        calcBtn.disabled = true;
        calcBtn.innerHTML = '<span class="material-symbols-outlined animate-spin">progress_activity</span> Hesaplama Yapılıyor...';

        // Form verilerini topla (Aradüğüm dahil)
        const data = {
            algorithm: selectedAlgInput.value,
            source: document.getElementById('source').value,
            target: document.getElementById('target').value,
            min_bandwidth: parseFloat(document.getElementById('min_bandwidth').value),
            w_rel: document.getElementById('w_rel').value,
            w_delay: document.getElementById('w_delay').value,
            w_res: document.getElementById('w_res').value,
        };

        try {
            const response = await fetch('/calculate_route', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data),
            });

            const result = await response.json();

            if (response.ok) {
                // BAŞARILI YANIT İŞLEME
                
                // Metrikleri Güncelle
                totalCostDisplay.textContent = result.total_cost;
                relVal.textContent = `${result.reliability}%`;
                delayVal.textContent = `${result.delay}ms`;
                // Kaynak Kullanımı: (Sıfırdan büyük veya 100'den küçükse göster)
                usageVal.textContent = `${Math.min(100, Math.max(0, parseFloat(result.usage))).toFixed(2)}%`; 

                // Yol Görüntüsünü Güncelle
                pathDisplay.innerHTML = result.path.map((node, index) => {
                    if (index === result.path.length - 1) {
                        return `<span>${node}</span>`;
                    }
                    return `<span>${node}</span> <span class="material-symbols-outlined text-sm">arrow_forward</span>`;
                }).join('');
                
                // Görseli Güncelle
                if (result.graph_image) {
                    networkGraphImg.src = `data:image/png;base64,${result.graph_image}`;
                    networkGraphImg.classList.remove('hidden');
                    graphPlaceholder.classList.add('hidden');
                }
                
                // Debug Çıktısını Göster
                resultDisplay.textContent = result.debug;
                
                // GENİŞLETİLMİŞ SİMÜLASYON SONUÇLARINI GÖSTER
                const sim = result.sim_results;
                extraResultsContainer.innerHTML = `
                    <h4 class="text-sm font-bold text-text-sub uppercase mb-3 tracking-wide">Genişletilmiş Analiz</h4>
                    <div class="space-y-2 text-sm">
                        <p class="flex justify-between font-bold">Toplam Segment Sayısı: <span>${sim.total_segments}</span></p>
                        <p class="flex justify-between">Toplam Kenar (Hop) Sayısı: <span>${sim.path_length_hops}</span></p>
                        <p class="flex justify-between">Darboğaz (Min) Kapasite: <span class="text-red-400">${sim.bottleneck_capacity.toFixed(2)} mbps</span></p>
                        <p class="flex justify-between">Maksimum Kapasite: <span>${sim.max_capacity.toFixed(2)} mbps</span></p>
                        <p class="flex justify-between">Güvenilirlik Maliyeti (-log R): <span>${sim.reliability_cost.toFixed(4)}</span></p>
                    </div>
                `;


            } else {
                // HATA YANITI İŞLEME (400, 404, 500 vb.)
                const errorMessage = result.error || "Bilinmeyen bir hata oluştu.";
                
                // Sonuç alanlarını sıfırla
                totalCostDisplay.textContent = '--.--';
                pathDisplay.textContent = errorMessage;
                relVal.textContent = '--%';
                delayVal.textContent = '--ms';
                usageVal.textContent = '--%';

                // Görseli gizle
                networkGraphImg.classList.add('hidden');
                graphPlaceholder.classList.remove('hidden');
                
                // Debug alanını hata mesajıyla doldur
                resultDisplay.textContent = `HATA: ${errorMessage}\n\nTam Yanıt: ${JSON.stringify(result, null, 2)}`;
                
                // Genişletilmiş sonuçları temizle
                extraResultsContainer.innerHTML = ''; 
            }

        } catch (error) {
            // Ağ veya bağlantı hatası
            resultDisplay.textContent = `KRİTİK HATA: Sunucuya ulaşılamadı. Sunucunun (app.py) çalıştığından emin olun. Detay: ${error.message}`;
        } finally {
            // Butonu tekrar etkinleştir
            calcBtn.disabled = false;
            calcBtn.innerHTML = '<span class="material-symbols-outlined">play_circle</span> Optimal Rotayı Hesapla';
        }

        function syncRangeAndNumber(rangeId, numberId) {
            const range = document.getElementById(rangeId);
            const number = document.getElementById(numberId);
        
            if (!range || !number) return;
        
            // Slider hareket ettiğinde number input güncellensin
    range.addEventListener('input', () => {
        number.value = range.value;
    });

    // Number input değişirse slider güncellensin
    number.addEventListener('input', () => {
        let val = parseFloat(number.value);
        if (isNaN(val)) return;

        val = Math.min(1, Math.max(0, val));
        range.value = val;
        number.value = val;
    });
}

// Örnek: güvenilirlik slider + number input
syncRangeAndNumber('w_rel', 'w_rel_number');
syncRangeAndNumber('w_delay', 'w_delay_number');
syncRangeAndNumber('w_res', 'w_res_number');
        
    });
});