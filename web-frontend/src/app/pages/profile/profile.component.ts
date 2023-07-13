import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormControl, FormGroup } from "@angular/forms";
import { UserSettingsService } from "../../user-settings.service";
import { User } from "../../rest-api";

@Component({
  selector: 'app-profile',
  templateUrl: './profile.component.html',
  styleUrls: ['./profile.component.scss']
})
export class ProfileComponent implements OnInit {
  accountForm!: FormGroup;
  passwordForm!: FormGroup;
  imageSrc?: string;
  imageFile?: File;
  changePassword: boolean = false;
  showAccountPassword: boolean = false;
  showConfirmPassword: boolean = false;

  constructor(private formBuilder: FormBuilder, private settings: UserSettingsService) {
  }
  ngOnInit() {
    this.settings.user$.subscribe(user => {
      this.imageSrc = user?.profile.icon;
      this.fillForms(user)
    });
  }

  fillForms(user: User | undefined) {
    this.accountForm = this.formBuilder.group({
      username: user?.username || '',
      firstName: user?.first_name || '',
      lastName: user?.last_name || ''
    });
    this.passwordForm = this.formBuilder.group({
      password: new FormControl({ value: '', disabled: !this.changePassword }),
      confirmPass: new FormControl({ value: '', disabled: !this.changePassword })
    });
  }

  onTogglePassChange(checked: boolean) {
    this.changePassword = checked;
    if (checked){
      this.passwordForm.controls['password'].enable();
      this.passwordForm.controls['confirmPass'].enable();
    }
    else {
      this.passwordForm.controls['password'].disable();
      this.passwordForm.controls['confirmPass'].disable();
    }
  }

  onImageChange(files: FileList) {
    if (!files.length) return;
    this.imageFile = files[0];
    const reader = new FileReader();
    reader.readAsDataURL(this.imageFile);
    reader.onload = () => {
      this.imageSrc = reader.result as string;
      // this.myForm.patchValue({
      //   fileSource: reader.result
      // });
    }
  }
}
