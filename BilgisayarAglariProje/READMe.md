bilgisayar Ağları projesi 

1.Proje hakkında
Bu proje,karmaşık bir ağ topolojisinde belirlenen QoS parametrelerine (gecikme, güvenilirlik, kaynak kullanımı) göre en optimal rotayı bulmaktır.

2.Kullanılan teknolojiler ve kütüphaneler
Dil: Python 3.x
Arayüz: Flask (Web tabanlı görselleştirme)
Veri Analizi: Pandas, Numpy
Graf İşlemleri: NetworkX
Görselleştirme: Matplotlib

3.Çalıştırma adımları
Projeyi bilgisayarınızda çalıştırmak için:
Projenin çalışması için Python 3.8+ gereklidir. Gerekli tüm kütüphaneleri tek seferde yüklemek için terminale şu komutu yazın:
#pip install -r requirements.txt
Tarayıcınızda http://127.0.0.1:5000 adresini açın.
Başlangıç (Source) ve Hedef (Destination) düğümlerini seçip "Çalıştır" butonuna basın.

4.Seed Bilgisi
Algoritmaların ACO_algorithm.py, genetik_alg.py ve QLearning_algorithm.py dosyalarında random.seed(42) ve np.random.seed(42) komutları uygulanmıştır. her çalışmada aynı sonucu vermesi için kod içerisinde Seed: 42 kullanılmıştır. 

Kod:random.seed(42) ve np.random.seed(42)

1.Karınca Kolonisi Optimizasyonu (ACO)
Doğadaki karıncaların yiyecek bulmak için bıraktıkları feromon izlerini taklit eder.

İşleyiş: Her iterasyonda "karınca" olarak adlandırılan ajanlar, kaynak düğümden yola çıkar. Bir sonraki düğümü seçerken hem mevcut feromon miktarını (deneyim) hem de kenarın QoS maliyetini (sezgisel bilgi) dikkate alırlar.

Güncelleme:İyi sonuç veren yollardaki feromon miktarı artırılırken, kötü yollardaki feromonlar zamanla buharlaşır (evaporation).

Projedeki Rolü:Dinamik ve olasılıksal yapısı sayesinde gecikme ve güvenilirlik dengesini kurmakta etkilidir.

2.Genetik Algoritma (GA)
Darwin’in evrim teorisindeki "en iyi olan hayatta kalır" prensibine dayanır.

Popülasyon: Başlangıçta rastgele yollardan (bireylerden) oluşan bir küme oluşturulur.

Seçilim & Çaprazlama: Düşük maliyetli (fitness değeri yüksek) yollar seçilir ve bu yolların parçaları birleştirilerek (crossover) yeni "çocuk yollar" üretilir.

Mutasyon: Rotalarda rastgele değişiklikler yapılarak algoritmanın yerel minimuma sıkışması engellenir.

Projedeki Rolü: Çok geniş arama uzaylarında farklı QoS kombinasyonlarını keşfetmekte çok başarılıdır.

3.Q-Learning (Pekiştirmeli Öğrenme)
Bir ajanın çevreyle etkileşime girerek "deneme-yanılma" yoluyla öğrenmesini sağlar.

Q-Tablosu: Her düğüm ve komşusu için bir "Q-değeri" (kalite değeri) tutulur.

Ödül Mekanizması: Ajan hedefe ulaştığında, geçtiği yoldaki QoS değerlerine göre pozitif bir ödül alır. Eğer yol kısıtları (bant genişliği gibi) ihlal edilirse negatif ceza alır.

Eğitim:Binlerce iterasyon (episode) sonunda ajan, hangi düğümden hangisine gitmesi gerektiğini öğrenen bir harita (Q-Table) oluşturur.

Projedeki Rolü: Sabit topolojilerde bir kez eğitildikten sonra en hızlı ve en kararlı kararı veren yöntemdir.

Arayüz üzerinden Kaynak Düğüm, Hedef Düğüm ve Bant Genişliği değerlerini girerek algoritmaları test edebilirsiniz.

5.Optimizasyon metrikleri ve formülasyon 
Proje, çok amaçlı bir optimizasyon problemini çözmekte olup, aşağıdaki formül (Weighted Sum Method) baz alınmıştır:
$$Cost = (w delay. TotalDelay) + (w_reliability .(-log(Reliability))) + (w_resource.ResourceCost)
Kısıt: Bandwidth_link >= Demand_user (Bu şartı sağlamayan linkler rota dışı bırakılır)
Amaç: Toplam maliyeti (Cost) minimize etmek.

6.Proje süreci, mühendislik disiplinine uygun olarak aşağıdaki şekilde paylaştırılmıştır:

1.Şeyda Nur Okcu --- > Görev:ağ kısımını csv dosyalarına göre oluşturması.
2.Sümeyye Çakır ---> Görev:Optimizasyon kısmının toplam gecikme ,toplam güvenilirlik ,Ağ Kaynak Kullanımı  kodalaması.
3.Ahmet taha Yalçın ---> Görev:Algoritmaların test edilmesi ve tablo tasarımı. 
4.Abdullah Walidi ---> Görev: Karınca kolonisi (ACO) algoritması tasarımı.
5.İlayda Karaca ---> Görev: Genetik (GE) algoritması tasarımı.
6.Salih Unat ---> Görev: Q learning algoritması tasarımı.
7.Sina Rahbaribanaeian ---> Görev: Mimarinin kurulması ve modüller arası veri akış kontrolü,README/Rapor hazırlığı.
8.Manal Idrees Abbas Abbas ---> Görev : Arayüz tasarımı ve projenin demo halinin video çekimi.

7.Proje dosya yapısı
app.py:Ana uygulama ve API servisleri.

Ag_olusturma.py:Veri tabanı işlemleri ve temel metrik hesaplamaları.

ACO_algorithm.py:Karınca kolonisi modülü.

genetik_alg.py:Genetik algoritma modülü.

QLearning_algorithm.py:Pekiştirmeli öğrenme modülü.

templates/: Arayüz dosyaları (HTML).

7.Önemli notlar
Yorum satırları: Her fonksiyonun üzerinde amacı, parametreleri ve dönüş değerleri detaylıca açıklanmıştır.

Hata yönetimi: Kaynak ve hedef arasında yol bulunamadığı durumlarda sistem güvenli hata mesajları döndürmektedir.

Performans: Algoritmalar, büyük ölçekli grafikleri (1000+ düğüm kapasiteli) işleyebilecek şekilde optimize edilmiştir.
