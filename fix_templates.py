import os
import re

router_dir = r"c:\ServBay\www\eka-ai-debugger\app\routers"

# We want to replace:
# sablonlar.TemplateResponse("xxx.html", {...})
# with:
# sablonlar.TemplateResponse(request=request, name="xxx.html", context={...})

for filename in os.listdir(router_dir):
    if filename.endswith(".py"):
        filepath = os.path.join(router_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Regex to capture the arguments.
        # It usually looks like: sablonlar.TemplateResponse("auth/login.html", {"request": request, "hata": "E-posta veya şifre hatalı."})
        # We can just replace: sablonlar.TemplateResponse(
        # with: sablonlar.TemplateResponse(request=request, name=
        # Wait, if we do that, we also need context=. We can just replace:
        # sablonlar.TemplateResponse(" to sablonlar.TemplateResponse(request=request, name="
        # Then we need to replace the `, {` with `, context={`.
        # A simpler regex:
        # re.sub(r'sablonlar\.TemplateResponse\((["\'].*?["\']),\s*(\{.*?\})\)', r'sablonlar.TemplateResponse(request=request, name=\1, context=\2)', content, flags=re.DOTALL)
        
        # In oturumlar.py we have Multiline dicts:
        # return sablonlar.TemplateResponse("sessions/detail.html", {
        #    "request": request,
        #    "kullanici": kullanici,
        #    "oturum": oturum,
        #    "rapor": rapor
        # })
        new_content = re.sub(
            r'sablonlar\.TemplateResponse\(\s*(["\'][^"\']+["\'])\s*,\s*(\{.*?\})\s*\)',
            r'sablonlar.TemplateResponse(request=request, name=\1, context=\2)',
            content,
            flags=re.DOTALL
        )
        
        if new_content != content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Fixed {filename}")

