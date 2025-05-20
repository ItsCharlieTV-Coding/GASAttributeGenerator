import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import json
import os

def to_identifier(name):
    return ''.join(c if c.isalnum() else '_' for c in name)

def generate_code(attributes, replicated, api_macro, class_name, base_class):
    class_name_u = f"U{class_name}"
    header_file = f"{class_name}.h"
    cpp_file = f"{class_name}.cpp"

    base_class_u = base_class if base_class.startswith('U') else f"U{base_class}"
    include_name = base_class[1:] if base_class.startswith('U') else base_class

    header = f'''#pragma once

#include "CoreMinimal.h"
#include "{include_name}.h"
#include "AbilitySystemComponent.h"
#include "GameplayEffectExtension.h"
#include "{class_name}.generated.h"

#define ATTRIBUTE_ACCESSORS(ClassName, PropertyName) \\
    GAMEPLAYATTRIBUTE_PROPERTY_GETTER(ClassName, PropertyName) \\
    GAMEPLAYATTRIBUTE_VALUE_GETTER(PropertyName) \\
    GAMEPLAYATTRIBUTE_VALUE_SETTER(PropertyName) \\
    GAMEPLAYATTRIBUTE_VALUE_INITTER(PropertyName)

UCLASS()
class {api_macro} {class_name_u} : public {base_class_u}
{{
    GENERATED_BODY()

public:
    {class_name_u}();

'''

    for attr in attributes:
        id = to_identifier(attr)
        if attr in replicated:
            header += f'''    UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_{id}, Category = "Attributes")
    FGameplayAttributeData {id};
    ATTRIBUTE_ACCESSORS({class_name_u}, {id})

'''
        else:
            header += f'''    UPROPERTY(BlueprintReadOnly, Category = "Attributes")
    FGameplayAttributeData {id};
    ATTRIBUTE_ACCESSORS({class_name_u}, {id})

'''

    for attr in replicated:
        id = to_identifier(attr)
        header += f'''    UFUNCTION()
    void OnRep_{id}(const FGameplayAttributeData& Old{id});

'''

    header += '''    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;
};
'''

    cpp = f'''#include "{header_file}"
#include "Net/UnrealNetwork.h"
#include "GameplayEffectExtension.h"

{class_name_u}::{class_name_u}()
{{
}}

void {class_name_u}::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const
{{
    Super::GetLifetimeReplicatedProps(OutLifetimeProps);
'''

    for attr in replicated:
        id = to_identifier(attr)
        cpp += f'    DOREPLIFETIME_CONDITION_NOTIFY({class_name_u}, {id}, COND_None, REPNOTIFY_Always);\n'

    cpp += '}\n\n'

    for attr in replicated:
        id = to_identifier(attr)
        cpp += f'''void {class_name_u}::OnRep_{id}(const FGameplayAttributeData& Old{id})
{{
    GAMEPLAYATTRIBUTE_REPNOTIFY({class_name_u}, {id}, Old{id});
}}

'''

    with open(header_file, 'w', encoding='utf-8') as f:
        f.write(header)
    with open(cpp_file, 'w', encoding='utf-8') as f:
        f.write(cpp)

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _, _ = self.widget.bbox("insert") or (0,0,0,0)
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class AttributeUI:
    def __init__(self, root):
        self.root = root
        self.root.title("AttributeSet Generator")

        self.settings_file = "settings.json"
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        tk.Label(self.root, text="Replicated Attributes (one per line):").grid(row=0, column=0, padx=5, pady=5)
        tk.Label(self.root, text="Non-Replicated Attributes (one per line):").grid(row=0, column=1, padx=5, pady=5)

        self.replicated_input = ScrolledText(self.root, height=10, width=30)
        self.replicated_input.grid(row=1, column=0, padx=5, pady=5)

        self.nonreplicated_input = ScrolledText(self.root, height=10, width=30)
        self.nonreplicated_input.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(self.root, text="API Macro:").grid(row=2, column=0, sticky="e")
        self.api_entry = tk.Entry(self.root)
        self.api_entry.grid(row=2, column=1, sticky="w")
        ToolTip(self.api_entry, "The API macro used in UCLASS (e.g., MYGAME_API)")

        tk.Label(self.root, text="Class Name (no extension):").grid(row=3, column=0, sticky="e")
        self.class_entry = tk.Entry(self.root)
        self.class_entry.grid(row=3, column=1, sticky="w")
        ToolTip(self.class_entry, "Name used to generate MyClass.h and MyClass.cpp")

        tk.Label(self.root, text="Base Class Name:").grid(row=4, column=0, sticky="e")
        self.base_entry = tk.Entry(self.root)
        self.base_entry.grid(row=4, column=1, sticky="w")
        ToolTip(self.base_entry, "Base class to inherit from (e.g., MyBaseSet)")

        self.generate_btn = tk.Button(self.root, text="Generate Files", command=self.generate_files)
        self.generate_btn.grid(row=5, column=0, pady=10)

        self.save_btn = tk.Button(self.root, text="Save Settings", command=self.save_settings)
        self.save_btn.grid(row=5, column=1, pady=10)

    def generate_files(self):
        replicated = [line.strip() for line in self.replicated_input.get("1.0", tk.END).splitlines() if line.strip()]
        nonreplicated = [line.strip() for line in self.nonreplicated_input.get("1.0", tk.END).splitlines() if line.strip()]
        all_attrs = replicated + nonreplicated

        if not all_attrs:
            messagebox.showerror("Error", "Please enter at least one attribute.")
            return

        api_macro = self.api_entry.get().strip()
        class_name = self.class_entry.get().strip()
        base = self.base_entry.get().strip()

        if not class_name:
            messagebox.showerror("Error", "Please enter a class name.")
            return

        generate_code(all_attrs, replicated, api_macro, class_name, base)
        messagebox.showinfo("Success", f"{class_name}.h and {class_name}.cpp generated.")

    def save_settings(self):
        settings = {
            "replicated": self.replicated_input.get("1.0", tk.END),
            "nonreplicated": self.nonreplicated_input.get("1.0", tk.END),
            "api_macro": self.api_entry.get().strip(),
            "class_name": self.class_entry.get().strip(),
            "base_class": self.base_entry.get().strip()
        }

        with open(self.settings_file, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)
        messagebox.showinfo("Saved", "Settings saved successfully.")

    def load_settings(self):
        if not os.path.exists(self.settings_file):
            return
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            self.replicated_input.insert("1.0", settings.get("replicated", ""))
            self.nonreplicated_input.insert("1.0", settings.get("nonreplicated", ""))
            self.api_entry.insert(0, settings.get("api_macro", ""))
            self.class_entry.insert(0, settings.get("class_name", ""))
            self.base_entry.insert(0, settings.get("base_class", ""))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AttributeUI(root)
    root.mainloop()
