-- phpMyAdmin SQL Dump
-- version 5.2.2
-- https://www.phpmyadmin.net/
--
-- Anamakine: localhost
-- Üretim Zamanı: 20 Nis 2026, 17:40:34
-- Sunucu sürümü: 11.4.5-MariaDB-log
-- PHP Sürümü: 7.4.33

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Veritabanı: `eka_ai_debugger`
--

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `bilgi_tabani_kayitlari`
--

CREATE TABLE `bilgi_tabani_kayitlari` (
  `id` int(11) NOT NULL,
  `kullanici_id` int(11) NOT NULL,
  `calisma_alani_id` int(11) DEFAULT NULL,
  `kaynak_oturum_id` int(11) DEFAULT NULL,
  `baslik` varchar(255) NOT NULL,
  `kategori` varchar(100) DEFAULT NULL,
  `etiketler_metin` varchar(500) DEFAULT NULL,
  `ozet` text DEFAULT NULL,
  `icerik` text NOT NULL,
  `durum` varchar(50) DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL,
  `guncellenme_tarihi` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `calisma_alani_uyeleri`
--

CREATE TABLE `calisma_alani_uyeleri` (
  `id` int(11) NOT NULL,
  `calisma_alani_id` int(11) NOT NULL,
  `kullanici_id` int(11) NOT NULL,
  `rol` varchar(50) DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `calisma_alanlari`
--

CREATE TABLE `calisma_alanlari` (
  `id` int(11) NOT NULL,
  `isim` varchar(255) NOT NULL,
  `sahip_id` int(11) NOT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL,
  `aciklama` text DEFAULT NULL,
  `aktif_mi` tinyint(1) DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Tablo döküm verisi `calisma_alanlari`
--

INSERT INTO `calisma_alanlari` (`id`, `isim`, `sahip_id`, `olusturulma_tarihi`, `aciklama`, `aktif_mi`) VALUES
(1, 'Eka Kurumsal', 1, NULL, NULL, 1),
(2, 'Kişisel Çalışma Alanı', 2, '2026-04-20 04:55:25', NULL, 1),
(3, 'Kişisel Çalışma Alanı', 3, '2026-04-20 06:30:28', NULL, 1);

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `hata_otirumlari`
--

CREATE TABLE `hata_otirumlari` (
  `id` int(11) NOT NULL,
  `calisma_alani_id` int(11) NOT NULL,
  `olusturan_id` int(11) NOT NULL,
  `baslik` varchar(255) NOT NULL,
  `programlama_dili` varchar(100) NOT NULL,
  `kod_parcasi` text NOT NULL,
  `hata_logu` text DEFAULT NULL,
  `yigin_izleme` text DEFAULT NULL,
  `ek_notlar` text DEFAULT NULL,
  `durum` varchar(50) DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL,
  `benzer_oturum_id` int(11) DEFAULT NULL,
  `etiketler_metin` varchar(500) DEFAULT NULL,
  `secilen_saglayici` varchar(100) DEFAULT NULL,
  `secilen_model` varchar(255) DEFAULT NULL,
  `baglam_ozeti` text DEFAULT NULL,
  `benzerlik_skoru` float DEFAULT NULL,
  `tahmini_girdi_tokeni` int(11) DEFAULT 0,
  `tahmini_cikti_tokeni` int(11) DEFAULT 0,
  `tahmini_maliyet` float DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Tablo döküm verisi `hata_otirumlari`
--

INSERT INTO `hata_otirumlari` (`id`, `calisma_alani_id`, `olusturan_id`, `baslik`, `programlama_dili`, `kod_parcasi`, `hata_logu`, `yigin_izleme`, `ek_notlar`, `durum`, `olusturulma_tarihi`, `benzer_oturum_id`, `etiketler_metin`, `secilen_saglayici`, `secilen_model`, `baglam_ozeti`, `benzerlik_skoru`, `tahmini_girdi_tokeni`, `tahmini_cikti_tokeni`, `tahmini_maliyet`) VALUES
(1, 2, 2, 'test', 'PHP', 'test', 'test', 'test', '', 'tamamlandi', '2026-04-20 05:10:14', NULL, NULL, NULL, NULL, NULL, NULL, 0, 0, 0);

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `hata_oturum_dosyalari`
--

CREATE TABLE `hata_oturum_dosyalari` (
  `id` int(11) NOT NULL,
  `oturum_id` int(11) NOT NULL,
  `dosya_adi` varchar(255) NOT NULL,
  `orijinal_ad` varchar(255) NOT NULL,
  `icerik_tipi` varchar(120) DEFAULT NULL,
  `boyut` int(11) DEFAULT NULL,
  `kayit_yolu` varchar(500) NOT NULL,
  `metin_icerigi` text DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `hata_raporlari`
--

CREATE TABLE `hata_raporlari` (
  `id` int(11) NOT NULL,
  `oturum_id` int(11) NOT NULL,
  `kok_neden` text DEFAULT NULL,
  `onem_derecesi` varchar(50) DEFAULT NULL,
  `etkilenen_katman` varchar(100) DEFAULT NULL,
  `cozum_onerileri` text DEFAULT NULL,
  `iyilestirilmis_kod` text DEFAULT NULL,
  `guvenlik_notlari` text DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Tablo döküm verisi `hata_raporlari`
--

INSERT INTO `hata_raporlari` (`id`, `oturum_id`, `kok_neden`, `onem_derecesi`, `etkilenen_katman`, `cozum_onerileri`, `iyilestirilmis_kod`, `guvenlik_notlari`, `olusturulma_tarihi`) VALUES
(1, 1, 'Sistem test sağlayıcısı tarafından tespit edilen örnek hata türü. Değişken başlatılmamış.', 'Orta', 'Arka Uç Veri İşleme', 'Değişkeni kullanmadan önce varsayılan bir değer ile başlatın. Null kontrolleri ekleyin.', '```python\ndef guvenli_islem(veri=None):\n    if veri is None:\n        veri = []\n    return len(veri)\n```', 'Girdi doğrudan kullanıldığı için potansiyel tip hatalarına yol açabilir.', '2026-04-20 05:10:14');

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `istem_sablonlari`
--

CREATE TABLE `istem_sablonlari` (
  `id` int(11) NOT NULL,
  `baslik` varchar(255) NOT NULL,
  `icerik` text NOT NULL,
  `versiyon` int(11) DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `kullanicilar`
--

CREATE TABLE `kullanicilar` (
  `id` int(11) NOT NULL,
  `ad_soyad` varchar(255) NOT NULL,
  `eposta` varchar(255) NOT NULL,
  `sifre_hash` varchar(255) NOT NULL,
  `rol` varchar(50) DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Tablo döküm verisi `kullanicilar`
--

INSERT INTO `kullanicilar` (`id`, `ad_soyad`, `eposta`, `sifre_hash`, `rol`, `olusturulma_tarihi`) VALUES
(1, 'Admin Eka', 'info@ekayazilim.com.tr', '$2b$12$qLiLaBsLux.2GJdaAXRqyORrISj043mgO/Pnn4yGILCEj1k/9K/t6', 'admin', '2026-03-03 17:37:12'),
(2, 'Eka Test', 'admin@ekayazilim.com', '$2b$12$qLiLaBsLux.2GJdaAXRqyORrISj043mgO/Pnn4yGILCEj1k/9K/t6', 'kullanici', '2026-04-20 04:55:25'),
(3, 'Eka Sunucu', 'ekasunucu@gmail.com', '$2b$12$qLiLaBsLux.2GJdaAXRqyORrISj043mgO/Pnn4yGILCEj1k/9K/t6', 'admin', '2026-04-20 06:30:28');

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `kullanici_ayarlari`
--

CREATE TABLE `kullanici_ayarlari` (
  `id` int(11) NOT NULL,
  `kullanici_id` int(11) NOT NULL,
  `secili_saglayici_id` int(11) DEFAULT NULL,
  `secili_model` varchar(100) DEFAULT NULL,
  `aktif_calisma_alani_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Tablo döküm verisi `kullanici_ayarlari`
--

INSERT INTO `kullanici_ayarlari` (`id`, `kullanici_id`, `secili_saglayici_id`, `secili_model`, `aktif_calisma_alani_id`) VALUES
(1, 1, NULL, NULL, 1),
(2, 2, NULL, NULL, 2),
(4, 3, NULL, NULL, 3);

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `sistem_gunlukleri`
--

CREATE TABLE `sistem_gunlukleri` (
  `id` int(11) NOT NULL,
  `kullanici_id` int(11) DEFAULT NULL,
  `islem_tipi` varchar(100) NOT NULL,
  `detaylar` text DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `yapay_zeka_istekleri`
--

CREATE TABLE `yapay_zeka_istekleri` (
  `id` int(11) NOT NULL,
  `oturum_id` int(11) NOT NULL,
  `saglayici` varchar(100) NOT NULL,
  `istek_icerigi` text NOT NULL,
  `yanit_icerigi` text DEFAULT NULL,
  `basarili` tinyint(1) DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL,
  `model` varchar(255) DEFAULT NULL,
  `girdi_tokeni` int(11) DEFAULT 0,
  `cikti_tokeni` int(11) DEFAULT 0,
  `toplam_tokeni` int(11) DEFAULT 0,
  `tahmini_maliyet` float DEFAULT 0,
  `gecikme_ms` int(11) DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Tablo döküm verisi `yapay_zeka_istekleri`
--

INSERT INTO `yapay_zeka_istekleri` (`id`, `oturum_id`, `saglayici`, `istek_icerigi`, `yanit_icerigi`, `basarili`, `olusturulma_tarihi`, `model`, `girdi_tokeni`, `cikti_tokeni`, `toplam_tokeni`, `tahmini_maliyet`, `gecikme_ms`) VALUES
(1, 1, 'mock', 'Programlama Dili: PHP\nKod:\ntest\nHata Logu:\ntest\nYığın İzleme:\ntest\nNotlar:\n', '{\"kok_neden\": \"Sistem test sa\\u011flay\\u0131c\\u0131s\\u0131 taraf\\u0131ndan tespit edilen \\u00f6rnek hata t\\u00fcr\\u00fc. De\\u011fi\\u015fken ba\\u015flat\\u0131lmam\\u0131\\u015f.\", \"onem_derecesi\": \"Orta\", \"etkilenen_katman\": \"Arka U\\u00e7 Veri \\u0130\\u015fleme\", \"cozum_onerileri\": \"De\\u011fi\\u015fkeni kullanmadan \\u00f6nce varsay\\u0131lan bir de\\u011fer ile ba\\u015flat\\u0131n. Null kontrolleri ekleyin.\", \"iyilestirilmis_kod\": \"```python\\ndef guvenli_islem(veri=None):\\n    if veri is None:\\n        veri = []\\n    return len(veri)\\n```\", \"guvenlik_notlari\": \"Girdi do\\u011frudan kullan\\u0131ld\\u0131\\u011f\\u0131 i\\u00e7in potansiyel tip hatalar\\u0131na yol a\\u00e7abilir.\"}', 1, '2026-04-20 05:10:14', NULL, 0, 0, 0, 0, 0);

-- --------------------------------------------------------

--
-- Tablo için tablo yapısı `yapay_zeka_saglayicilari`
--

CREATE TABLE `yapay_zeka_saglayicilari` (
  `id` int(11) NOT NULL,
  `ad` varchar(100) NOT NULL,
  `base_url` varchar(255) NOT NULL,
  `api_key` varchar(255) DEFAULT NULL,
  `modeller` text DEFAULT NULL,
  `aktif_mi` tinyint(1) DEFAULT NULL,
  `olusturulma_tarihi` datetime DEFAULT NULL,
  `kullanici_id` int(11) DEFAULT NULL,
  `saglayici_tipi` varchar(50) DEFAULT NULL,
  `gosterim_adi` varchar(100) DEFAULT NULL,
  `api_key_encrypted` text DEFAULT NULL,
  `api_key_masked` varchar(255) DEFAULT NULL,
  `varsayilan_model` varchar(255) DEFAULT NULL,
  `modeller_json` text DEFAULT NULL,
  `son_test_basarili` tinyint(1) DEFAULT 0,
  `son_test_mesaji` text DEFAULT NULL,
  `son_test_tarihi` datetime DEFAULT NULL,
  `son_gecikme_ms` int(11) DEFAULT 0,
  `son_basari_orani` float DEFAULT 0,
  `son_kullanim_tarihi` datetime DEFAULT NULL,
  `aylik_tahmini_maliyet` float DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Dökümü yapılmış tablolar için indeksler
--

--
-- Tablo için indeksler `bilgi_tabani_kayitlari`
--
ALTER TABLE `bilgi_tabani_kayitlari`
  ADD PRIMARY KEY (`id`),
  ADD KEY `kaynak_oturum_id` (`kaynak_oturum_id`),
  ADD KEY `ix_bilgi_tabani_kayitlari_calisma_alani_id` (`calisma_alani_id`),
  ADD KEY `ix_bilgi_tabani_kayitlari_id` (`id`),
  ADD KEY `ix_bilgi_tabani_kayitlari_kullanici_id` (`kullanici_id`);

--
-- Tablo için indeksler `calisma_alani_uyeleri`
--
ALTER TABLE `calisma_alani_uyeleri`
  ADD PRIMARY KEY (`id`),
  ADD KEY `calisma_alani_id` (`calisma_alani_id`),
  ADD KEY `kullanici_id` (`kullanici_id`),
  ADD KEY `ix_calisma_alani_uyeleri_id` (`id`);

--
-- Tablo için indeksler `calisma_alanlari`
--
ALTER TABLE `calisma_alanlari`
  ADD PRIMARY KEY (`id`),
  ADD KEY `sahip_id` (`sahip_id`),
  ADD KEY `ix_calisma_alanlari_id` (`id`);

--
-- Tablo için indeksler `hata_otirumlari`
--
ALTER TABLE `hata_otirumlari`
  ADD PRIMARY KEY (`id`),
  ADD KEY `calisma_alani_id` (`calisma_alani_id`),
  ADD KEY `olusturan_id` (`olusturan_id`),
  ADD KEY `ix_hata_otirumlari_id` (`id`);

--
-- Tablo için indeksler `hata_oturum_dosyalari`
--
ALTER TABLE `hata_oturum_dosyalari`
  ADD PRIMARY KEY (`id`),
  ADD KEY `oturum_id` (`oturum_id`),
  ADD KEY `ix_hata_oturum_dosyalari_id` (`id`);

--
-- Tablo için indeksler `hata_raporlari`
--
ALTER TABLE `hata_raporlari`
  ADD PRIMARY KEY (`id`),
  ADD KEY `oturum_id` (`oturum_id`),
  ADD KEY `ix_hata_raporlari_id` (`id`);

--
-- Tablo için indeksler `istem_sablonlari`
--
ALTER TABLE `istem_sablonlari`
  ADD PRIMARY KEY (`id`),
  ADD KEY `ix_istem_sablonlari_id` (`id`);

--
-- Tablo için indeksler `kullanicilar`
--
ALTER TABLE `kullanicilar`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ix_kullanicilar_eposta` (`eposta`),
  ADD KEY `ix_kullanicilar_id` (`id`);

--
-- Tablo için indeksler `kullanici_ayarlari`
--
ALTER TABLE `kullanici_ayarlari`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `kullanici_id` (`kullanici_id`),
  ADD KEY `secili_saglayici_id` (`secili_saglayici_id`),
  ADD KEY `ix_kullanici_ayarlari_id` (`id`);

--
-- Tablo için indeksler `sistem_gunlukleri`
--
ALTER TABLE `sistem_gunlukleri`
  ADD PRIMARY KEY (`id`),
  ADD KEY `kullanici_id` (`kullanici_id`),
  ADD KEY `ix_sistem_gunlukleri_id` (`id`);

--
-- Tablo için indeksler `yapay_zeka_istekleri`
--
ALTER TABLE `yapay_zeka_istekleri`
  ADD PRIMARY KEY (`id`),
  ADD KEY `oturum_id` (`oturum_id`),
  ADD KEY `ix_yapay_zeka_istekleri_id` (`id`);

--
-- Tablo için indeksler `yapay_zeka_saglayicilari`
--
ALTER TABLE `yapay_zeka_saglayicilari`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `ad` (`ad`),
  ADD KEY `ix_yapay_zeka_saglayicilari_id` (`id`);

--
-- Dökümü yapılmış tablolar için AUTO_INCREMENT değeri
--

--
-- Tablo için AUTO_INCREMENT değeri `bilgi_tabani_kayitlari`
--
ALTER TABLE `bilgi_tabani_kayitlari`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Tablo için AUTO_INCREMENT değeri `calisma_alani_uyeleri`
--
ALTER TABLE `calisma_alani_uyeleri`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Tablo için AUTO_INCREMENT değeri `calisma_alanlari`
--
ALTER TABLE `calisma_alanlari`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Tablo için AUTO_INCREMENT değeri `hata_otirumlari`
--
ALTER TABLE `hata_otirumlari`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Tablo için AUTO_INCREMENT değeri `hata_oturum_dosyalari`
--
ALTER TABLE `hata_oturum_dosyalari`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Tablo için AUTO_INCREMENT değeri `hata_raporlari`
--
ALTER TABLE `hata_raporlari`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Tablo için AUTO_INCREMENT değeri `istem_sablonlari`
--
ALTER TABLE `istem_sablonlari`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Tablo için AUTO_INCREMENT değeri `kullanicilar`
--
ALTER TABLE `kullanicilar`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Tablo için AUTO_INCREMENT değeri `kullanici_ayarlari`
--
ALTER TABLE `kullanici_ayarlari`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- Tablo için AUTO_INCREMENT değeri `sistem_gunlukleri`
--
ALTER TABLE `sistem_gunlukleri`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Tablo için AUTO_INCREMENT değeri `yapay_zeka_istekleri`
--
ALTER TABLE `yapay_zeka_istekleri`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Tablo için AUTO_INCREMENT değeri `yapay_zeka_saglayicilari`
--
ALTER TABLE `yapay_zeka_saglayicilari`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- Dökümü yapılmış tablolar için kısıtlamalar
--

--
-- Tablo kısıtlamaları `bilgi_tabani_kayitlari`
--
ALTER TABLE `bilgi_tabani_kayitlari`
  ADD CONSTRAINT `bilgi_tabani_kayitlari_ibfk_1` FOREIGN KEY (`kullanici_id`) REFERENCES `kullanicilar` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `bilgi_tabani_kayitlari_ibfk_2` FOREIGN KEY (`calisma_alani_id`) REFERENCES `calisma_alanlari` (`id`) ON DELETE SET NULL,
  ADD CONSTRAINT `bilgi_tabani_kayitlari_ibfk_3` FOREIGN KEY (`kaynak_oturum_id`) REFERENCES `hata_otirumlari` (`id`) ON DELETE SET NULL;

--
-- Tablo kısıtlamaları `calisma_alani_uyeleri`
--
ALTER TABLE `calisma_alani_uyeleri`
  ADD CONSTRAINT `calisma_alani_uyeleri_ibfk_1` FOREIGN KEY (`calisma_alani_id`) REFERENCES `calisma_alanlari` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `calisma_alani_uyeleri_ibfk_2` FOREIGN KEY (`kullanici_id`) REFERENCES `kullanicilar` (`id`) ON DELETE CASCADE;

--
-- Tablo kısıtlamaları `calisma_alanlari`
--
ALTER TABLE `calisma_alanlari`
  ADD CONSTRAINT `calisma_alanlari_ibfk_1` FOREIGN KEY (`sahip_id`) REFERENCES `kullanicilar` (`id`) ON DELETE CASCADE;

--
-- Tablo kısıtlamaları `hata_otirumlari`
--
ALTER TABLE `hata_otirumlari`
  ADD CONSTRAINT `hata_otirumlari_ibfk_1` FOREIGN KEY (`calisma_alani_id`) REFERENCES `calisma_alanlari` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `hata_otirumlari_ibfk_2` FOREIGN KEY (`olusturan_id`) REFERENCES `kullanicilar` (`id`) ON DELETE CASCADE;

--
-- Tablo kısıtlamaları `hata_oturum_dosyalari`
--
ALTER TABLE `hata_oturum_dosyalari`
  ADD CONSTRAINT `hata_oturum_dosyalari_ibfk_1` FOREIGN KEY (`oturum_id`) REFERENCES `hata_otirumlari` (`id`) ON DELETE CASCADE;

--
-- Tablo kısıtlamaları `hata_raporlari`
--
ALTER TABLE `hata_raporlari`
  ADD CONSTRAINT `hata_raporlari_ibfk_1` FOREIGN KEY (`oturum_id`) REFERENCES `hata_otirumlari` (`id`) ON DELETE CASCADE;

--
-- Tablo kısıtlamaları `kullanici_ayarlari`
--
ALTER TABLE `kullanici_ayarlari`
  ADD CONSTRAINT `kullanici_ayarlari_ibfk_1` FOREIGN KEY (`kullanici_id`) REFERENCES `kullanicilar` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `kullanici_ayarlari_ibfk_2` FOREIGN KEY (`secili_saglayici_id`) REFERENCES `yapay_zeka_saglayicilari` (`id`) ON DELETE SET NULL;

--
-- Tablo kısıtlamaları `sistem_gunlukleri`
--
ALTER TABLE `sistem_gunlukleri`
  ADD CONSTRAINT `sistem_gunlukleri_ibfk_1` FOREIGN KEY (`kullanici_id`) REFERENCES `kullanicilar` (`id`) ON DELETE SET NULL;

--
-- Tablo kısıtlamaları `yapay_zeka_istekleri`
--
ALTER TABLE `yapay_zeka_istekleri`
  ADD CONSTRAINT `yapay_zeka_istekleri_ibfk_1` FOREIGN KEY (`oturum_id`) REFERENCES `hata_otirumlari` (`id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
