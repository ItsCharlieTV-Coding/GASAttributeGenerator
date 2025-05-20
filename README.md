# GASAttributeGenerator

Hello and welcome to something I crafted to help myself generate GAS attributes. Hopefully it will help you. Its super straight forward. 

WARNING: You do need python to run this as its a python script. 

Open up the file and you will be presented with a few fields to fill out.

In the left pane, put all your attributes you wish to replicate e.g.

Health
MaxHealth
Mana
MaxMana

Put it in this format - one line for each attribute.

In the right pane, put all your non-replicated attributes e.g.

Damage
VoicelinePitch
HairLength

You then specify your API. This usually is your (your project name here)_API. For example: MYGAME_API

The next field is your AttributeSet Class Name. So this can be custom. For example: MyCharacterSet or EnemySet. Its not manditory to have Set at the end, but its good practise to keep everything uniform.

The Base Class feild is the parent class. So unless you have made your own AttributeSet class you which to dirive from, just keep Base Class as AttributeSet

You can save your settings if you wish.

Once you have done that, hit generate files! You now have your very own AttributeSet in C++ (You still have to install them/compile them into your project though)
