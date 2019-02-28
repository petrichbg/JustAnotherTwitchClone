from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from osp.models import UserData, UserNameChange
from datetime import datetime
import re #regexps

reserved_words = [
	'stat', 'rules', 'help', 'register', 'changelog', 'login', 'logout',
	'settings', 'users', 'stream', 'streams', 'following', 'api', 'service', 'dashboard',
	'markdown', 'bancheck', 'faq', 'admin', 'profile', 'chat',
]

# Create your forms here.
class DashboardStreamForm( forms.ModelForm ):
	class Meta:
		model = UserData
		fields = ( 'stream_description', 'stream_chat_motd', 'stream_hidden' )
		labels = {
			'stream_description': 'Название стрима',
			'stream_chat_motd': 'Сообщение дня в чате',
			'stream_hidden': 'Скрытый стрим',
		}
		widgets = {
			'stream_description': forms.TextInput( attrs = {
				'class': 'form-control',
				'placeholder': 'Безымянный стрим'
			} ),
			'stream_chat_motd': forms.TextInput( attrs = {
				'class': 'form-control',
				'placeholder': 'Сообщение дня отсутствует'
			} ),
		}

class UserSettingsProfileForm( forms.ModelForm ):
	remove_avatar = forms.BooleanField(
		label = "Удалить аватар:",
		required = False
	)

	class Meta:
		model = UserData
		fields = ( 'bio', 'avatar', 'show_subscriptions_on_top', 'receive_follow_notifications' )
		labels = {
			'bio': 'О себе и о стриме',
			'avatar': 'Аватар',
			'receive_follow_notifications': 'Получать оповещения о подписках на ваш канал'
		}
		widgets = {
			'bio': forms.Textarea( attrs = {
				'class': 'form-control'
			} ),
			'avatar': forms.ClearableFileInput( attrs = {
				'accept': '.jpg,.jpeg,.png,.gif'
			} ),
			'show_subscriptions_on_top': forms.CheckboxInput(),
			'receive_follow_notifications': forms.CheckboxInput(),
		}

class UserSettingsChangeNameForm( forms.Form ):
	def __init__( self, user, *args, **kwargs ):
		self.user = user
		super( UserSettingsChangeNameForm, self ).__init__( *args, **kwargs )

	new_username = forms.CharField(
		label = "Смена имени:",
		widget = forms.TextInput( attrs = {
			'class': 'form-control',
			'placeholder': 'Введите новое имя'
		} ),
		error_messages = {
			'required': 'Необходимо ввести новое имя'
		}
	)

	def clean( self ):
		#DRY issue with RegisterForm
		errors = []
		cleaned_data = super( UserSettingsChangeNameForm, self ).clean()
		new_username = cleaned_data.get( "new_username" )

		if new_username is None:
			errors.append( forms.ValidationError( "Необходимо ввести новое имя" ) )

		if new_username:
			if len( new_username ) < 3:
				#I don't want to subclass auth.user, so I'm checking it right here
				errors.append( forms.ValidationError( "Длина имени не должна быть меньше 3 символов" ) )
			new_username_is_correct = re.search( r"^[A-Za-z0-9]+(?:[_-][A-Za-z0-9]+)*$", new_username )
			if not new_username_is_correct:
				errors.append( forms.ValidationError( "Введеное вами имя неверно" ) )
			new_username_is_a_reserved_word = new_username.lower() in reserved_words
			if new_username_is_a_reserved_word:
				errors.append( forms.ValidationError( "Введеное вами имя недопустимо" ) )

		if User.objects.filter( username = new_username ).exists():
			errors.append( forms.ValidationError( "Данное имя пользователя уже занято" ) )

		DAYS_FOR_NEW_NAME_CHANGE = 365
		user_name_changes = UserNameChange.objects.filter( user = self.user.id ).order_by( '-change_date' )
		if len( user_name_changes ) > 0:
			current_date = datetime.now().date()
			last_name_change_date = user_name_changes[0].change_date
			days_passed = (current_date - last_name_change_date).days
			if days_passed < DAYS_FOR_NEW_NAME_CHANGE:
				errors.append( forms.ValidationError( "Возможность смены имени пока для вас недоступна" ) )

		if len( errors ) > 0:
			raise forms.ValidationError( errors )

class UserSettingsPasswordForm( PasswordChangeForm ):
	old_password = forms.CharField(
		label = "Текущий пароль:",
		widget = forms.PasswordInput(
			attrs = {
				'class': 'form-control',
				'placeholder': 'Введите текущий пароль'
			}
		),
		error_messages = {
			'required': 'Необходимо ввести подтверждение пароля'
		}
	)
	new_password1 = forms.CharField(
		label = "Новый пароль:",
		widget = forms.PasswordInput(
			attrs = {
				'class': 'form-control',
				'placeholder': 'Введите новый пароль'
			}
		),
		error_messages = {
			'required': 'Необходимо ввести новый пароль'
		}
	)
	new_password2 = forms.CharField(
		label = "Подтверждение нового пароля:",
		widget = forms.PasswordInput(
			attrs = {
				'class': 'form-control',
				'placeholder': 'Подтвердите новый пароль'
			}
		),
		error_messages = {
			'required': 'Необходимо ввести подтверждение нового пароля'
		}
	)
	error_messages = {
        'password_mismatch':  "Введенные пароли не совпадают",
		'password_incorrect':  "Введенный текущий пароль неверен",
    }

class UserSettingsDeleteYourselfForm( forms.Form ):
	def __init__( self, user, *args, **kwargs ):
		self.user = user
		super( UserSettingsDeleteYourselfForm, self ).__init__( *args, **kwargs )

	password = forms.CharField(
		label = "Пароль:",
		widget = forms.PasswordInput(
			attrs = {
				'class': 'form-control',
				'placeholder': 'Введите пароль'
			}
		),
		error_messages = {
			'required': 'Необходимо ввести пароль'
		}
	)

	def clean( self ):
		password = self.cleaned_data["password"]
		if not self.user.check_password( password ):
			raise forms.ValidationError( "Введенный пароль неверен" )

class RegisterForm( forms.ModelForm ):
	password_confirmation = forms.CharField(
		label = "Подтверждение пароля",
		widget = forms.PasswordInput(
			attrs = {
				'class': 'form-control',
				'placeholder': 'Подтвердите пароль'
			}
		),
		error_messages = {
			'required': 'Необходимо ввести подтверждение пароля'
		}
	)

	class Meta:
		model = User
		fields = ( 'username', 'password', 'password_confirmation' )
		labels = {
			'username': 'Имя пользователя',
			'password': 'Пароль',
			'password_confirmation': 'Подтверждение пароля'
		}
		widgets = {
			'username': forms.TextInput( attrs = {
				'class': 'form-control',
				'placeholder': 'Введите имя'
			} ),
			'password': forms.PasswordInput( attrs = {
				'class': 'form-control',
				'placeholder': 'Введите пароль'
			} )
		}
		error_messages = {
			'username': {
				'required': 'Необходимо ввести имя',
				'max_length': 'Длина имени превышает 30 символов',
				'unique': 'Данное имя пользователя уже занято',
				'invalid': 'Введеное вами имя неверно'
			},
			'password': {
				'required': 'Необходимо ввести пароль'
			}
		}

	def clean( self ):
		errors = []
		cleaned_data = super( RegisterForm, self ).clean()
		username = cleaned_data.get( "username" )
		if username:
			if len( username ) < 3:
				#I don't want to subclass auth.user, so I'm checking it right here
				errors.append( forms.ValidationError( "Длина имени не должна быть меньше 3 символов" ) )
			username_is_correct = re.search( r"^[A-Za-z0-9]+(?:[_-][A-Za-z0-9]+)*$", username )
			if not username_is_correct:
				errors.append( forms.ValidationError( "Введеное вами имя неверно" ) )
			username_is_a_reserved_word = username.lower() in reserved_words
			if username_is_a_reserved_word:
				errors.append( forms.ValidationError( "Введеное вами имя недопустимо" ) )

		password = cleaned_data.get( "password" )
		password_confirmation = cleaned_data.get( "password_confirmation" )
		if password and password_confirmation:
			if password != password_confirmation:
				errors.append( forms.ValidationError( "Введенные пароли не совпадают" ) )

		if len( errors ) > 0:
			raise forms.ValidationError( errors )

class LoginForm( forms.Form ):
	username = forms.CharField(
		widget = forms.TextInput(
			attrs = {
				'class': 'form-control',
				'placeholder': 'Введите имя'
			}
		),
		label = 'Имя',
		max_length = 30,
		error_messages = {
			'required': 'Необходимо ввести имя',
			'max_length': 'Длина имени превышает 30 символов',
		}
	)
	password = forms.CharField(
		widget = forms.PasswordInput(
			attrs = {
				'class': 'form-control',
				'placeholder': 'Введите пароль'
			}
		),
		label = 'Пароль',
		max_length = 30,
		error_messages = {
			'required': 'Необходимо ввести пароль'
		}
	)
