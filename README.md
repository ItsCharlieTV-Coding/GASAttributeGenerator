# Python-based GASAttributeGenerator

Welcome to **GASAttributeGenerator** — a tool I created to speed up the process of generating Gameplay Ability System (GAS) attribute sets in Unreal Engine. If you're working with GAS and find yourself repeatedly writing boilerplate code for attributes, this tool is here to help.

> ⚠️ **Note:** You need **Python** installed to run this script.

---

## 🚀 Features

- GUI-based attribute generation using **Tkinter**
- Supports both **replicated** and **non-replicated** attributes
- Automatically generates clean, uniform C++ code for your `AttributeSet` classes
- Supports custom class names, API macros, and base classes
- Optional settings saving

---

## 🛠 How to Use

1. **Run the Python Script**  
   Open the script using Python. A simple GUI will appear.

2. **Enter Your Attributes**  
   - **Replicated Attributes (Left Pane):**  
     Add each attribute you wish to replicate on its own line, e.g.:
     ```
     Health
     MaxHealth
     Mana
     MaxMana
     ```

   - **Non-Replicated Attributes (Right Pane):**  
     Add each non-replicated attribute on its own line, e.g.:
     ```
     Damage
     VoicelinePitch
     HairLength
     ```

3. **Set Your Configuration:**
   - **API Macro:**  
     Typically your project’s API macro, e.g. `MYGAME_API`.
   - **AttributeSet Class Name:**  
     Custom class name for your new `AttributeSet`, e.g. `MyCharacterSet` or `EnemySet`.  
     (It’s not required to end with "Set", but it's good practice.)
   - **Base Class:**  
     The parent class to inherit from. Use `AttributeSet` unless you have a custom one.

4. **Save Settings (Optional)**  
   If you'd like to reuse your configuration later.

5. **Generate Files**  
   Click the **Generate Files** button. Your new `AttributeSet` C++ files will be generated.

> 💡 Don't forget to include and compile the generated files in your Unreal Engine project.

---

## 📁 Output

The tool generates clean and structured `.h` and `.cpp` files with full support for replication (where applicable), getters/setters, and Unreal macros.

---

## 🧩 Requirements

- Python 3.x
- Tkinter (usually included with standard Python installations)

---

## 📬 Feedback

If you encounter bugs or have suggestions for improvement, feel free to open an issue or a pull request. I built this for myself, but I hope it helps others in the Unreal community too!

---

Happy developing! 🎮
