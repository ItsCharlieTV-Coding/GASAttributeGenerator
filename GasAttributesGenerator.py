import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import json
import os

def to_identifier(name):
    return ''.join(c if c.isalnum() else '_' for c in name)

def generate_code(attributes, replicated, api_macro, class_name, base_class):
    def to_identifier_local(name):
        return ''.join(c if c.isalnum() else '_' for c in name)

    class_name_u = f"U{class_name}"
    header_file = f"{class_name}.h"
    cpp_file = f"{class_name}.cpp"

    base_class_u = base_class if base_class.startswith('U') else f"U{base_class}"
    include_name = base_class[1:] if base_class.startswith('U') else base_class

    enum_values = [to_identifier_local(attr) for attr in attributes]

    enum_code = "UENUM(BlueprintType)\nenum class AllAttributesEnum : uint8\n{\n"
    for value in enum_values:
        enum_code += f"    {value} UMETA(DisplayName = \"{value}\"),\n"
    enum_code += "    None UMETA(Hidden)\n};\n\n"

    static_func_decl = (
        "    UFUNCTION(BlueprintPure, Category=\"Attributes\")\n"
        "    static AllAttributesEnum AttributeToEnum(const FGameplayAttribute& Attribute);\n\n"
    )

    header = (
        "#pragma once\n\n"
        "#include \"CoreMinimal.h\"\n"
        f"#include \"{include_name}.h\"\n"
        "#include \"AbilitySystemComponent.h\"\n"
        "#include \"GameplayEffectExtension.h\"\n"
        f"#include \"{class_name}.generated.h\"\n\n"
        f"{enum_code}"
        "#define ATTRIBUTE_ACCESSORS(ClassName, PropertyName) \\\n"
        "    GAMEPLAYATTRIBUTE_PROPERTY_GETTER(ClassName, PropertyName) \\\n"
        "    GAMEPLAYATTRIBUTE_VALUE_GETTER(PropertyName) \\\n"
        "    GAMEPLAYATTRIBUTE_VALUE_SETTER(PropertyName) \\\n"
        "    GAMEPLAYATTRIBUTE_VALUE_INITTER(PropertyName)\n\n"
    )

    # --- Delegate declarations (one per attribute) ---
    for attr in attributes:
        aid = to_identifier_local(attr)
        header += (
            "DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams("
            f"FOn{aid}Changed, float, OldValue, float, NewValue);\n"
        )
    header += "\n"

    header += (
        "UCLASS()\n"
        f"class {api_macro} {class_name_u} : public {base_class_u}\n"
        "{\n"
        "    GENERATED_BODY()\n\n"
        "public:\n"
        f"    {class_name_u}();\n\n"
        f"{static_func_decl}"
        "    virtual void GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const override;\n\n"
        "    // Fires on server and locally-authoritative changes (GameplayEffects, SetBaseValue, etc.)\n"
        "    virtual void PostAttributeChange(const FGameplayAttribute& Attribute, float OldValue, float NewValue) override;\n\n"
        "public:\n\n"
    )

    # --- Attributes + Accessors ---
    for attr in attributes:
        aid = to_identifier_local(attr)
        if attr in replicated:
            header += (
                "    UPROPERTY(BlueprintReadOnly, ReplicatedUsing = OnRep_"
                f"{aid}, Category = \"Attributes\")\n"
                f"    FGameplayAttributeData {aid};\n"
                f"    ATTRIBUTE_ACCESSORS({class_name_u}, {aid})\n\n"
            )
        else:
            header += (
                "    UPROPERTY(BlueprintReadOnly, Category = \"Attributes\")\n"
                f"    FGameplayAttributeData {aid};\n"
                f"    ATTRIBUTE_ACCESSORS({class_name_u}, {aid})\n\n"
            )

    # --- Events: delegate + BP event per attribute ---
    header += "    // Per-attribute change events\n"
    for attr in attributes:
        aid = to_identifier_local(attr)
        header += (
            f"    UPROPERTY(BlueprintAssignable, Category=\"Attributes|Events\")\n"
            f"    FOn{aid}Changed On{aid}Changed;\n\n"
            f"    UFUNCTION(BlueprintImplementableEvent, Category=\"Attributes|Events\")\n"
            f"    void BP_On{aid}Changed(float OldValue, float NewValue);\n\n"
        )

    # --- OnRep for replicated attributes ---
    for attr in replicated:
        aid = to_identifier_local(attr)
        header += (
            "    UFUNCTION()\n"
            f"    void OnRep_{aid}(const FGameplayAttributeData& Old{aid});\n\n"
        )

    header += "};\n"

    cpp = (
        f"#include \"{header_file}\"\n"
        "#include \"Net/UnrealNetwork.h\"\n"
        "#include \"GameplayEffectExtension.h\"\n\n"
        f"{class_name_u}::{class_name_u}()\n"
        "{\n"
        "}\n\n"
        f"void {class_name_u}::GetLifetimeReplicatedProps(TArray<FLifetimeProperty>& OutLifetimeProps) const\n"
        "{\n"
        "    Super::GetLifetimeReplicatedProps(OutLifetimeProps);\n"
    )

    for attr in replicated:
        aid = to_identifier_local(attr)
        cpp += (
            f"    DOREPLIFETIME_CONDITION_NOTIFY({class_name_u}, {aid}, COND_None, REPNOTIFY_Always);\n"
        )

    cpp += "}\n\n"

    # --- PostAttributeChange: fire per-attribute events on server/local changes ---
    cpp += (
        f"void {class_name_u}::PostAttributeChange(const FGameplayAttribute& Attribute, float OldValue, float NewValue)\n"
        "{\n"
        "    Super::PostAttributeChange(Attribute, OldValue, NewValue);\n\n"
        "    if (OldValue == NewValue)\n"
        "    {\n"
        "        return;\n"
        "    }\n\n"
    )

    for attr in attributes:
        aid = to_identifier_local(attr)
        cpp += (
            f"    if (Attribute == Get{aid}Attribute())\n"
            "    {\n"
            f"        On{aid}Changed.Broadcast(OldValue, NewValue);\n"
            f"        BP_On{aid}Changed(OldValue, NewValue);\n"
            "        return;\n"
            "    }\n\n"
        )

    cpp += "}\n\n"

    # --- OnRep: replicated attributes fire events on clients ---
    for attr in replicated:
        aid = to_identifier_local(attr)
        cpp += (
            f"void {class_name_u}::OnRep_{aid}(const FGameplayAttributeData& Old{aid})\n"
            "{\n"
            f"    GAMEPLAYATTRIBUTE_REPNOTIFY({class_name_u}, {aid}, Old{aid});\n"
            f"    const float OldValue = Old{aid}.GetCurrentValue();\n"
            f"    const float NewValue = {aid}.GetCurrentValue();\n"
            "    if (OldValue != NewValue)\n"
            "    {\n"
            f"        On{aid}Changed.Broadcast(OldValue, NewValue);\n"
            f"        BP_On{aid}Changed(OldValue, NewValue);\n"
            "    }\n"
            "}\n\n"
        )

    # --- AttributeToEnum implementation ---
    cpp += f"AllAttributesEnum {class_name_u}::AttributeToEnum(const FGameplayAttribute& Attribute)\n"
    cpp += "{\n"
    cpp += "    const FString AttributeName = Attribute.GetName();\n"
    for value in enum_values:
        cpp += f"    if (AttributeName == TEXT(\"{value}\")) return AllAttributesEnum::{value};\n"
    cpp += "    return AllAttributesEnum::None;\n"
    cpp += "}\n"

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
