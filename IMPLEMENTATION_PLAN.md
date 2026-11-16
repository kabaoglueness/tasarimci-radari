# StudioFinder — Android Capacitor APK & Güvenli Yayın Planı

- [x] Adım 1: `.gitignore` güncellemesi (`android/app/build/`, `.gradle/`, yerel anahtarlar)
- [x] Adım 2: `package.json` ve Capacitor bağımlılıklarının (`@capacitor/core`, `@capacitor/cli`, `@capacitor/android`) kurulması
- [x] Adım 3: İki katmanlı güvenli API motoru — `src/engine.js` içerisine yerel ağ sunucu IP ayarı ve GitHub placeholder fallback mekanizmasının eklenmesi
- [x] Adım 4: Arayüze minimal, şık mobil "Sunucu Bağlantı Ayarları" modalının eklenmesi (`index.html` & `src/app.js`)
- [x] Adım 5: Capacitor Android projesinin oluşturulması (`npx cap init` & `npx cap add android`)
- [x] Adım 6: Android Manifest, Cleartext HTTP izinleri ve derleme doğrulaması
