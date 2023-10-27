import { AfterViewInit, Component, EventEmitter, Inject, Output, TemplateRef } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from "@angular/material/dialog";
import { BehaviorSubject } from "rxjs";

interface DialogData {
  title?: string,
  message?: string,
  template: TemplateRef<any>,
  context?: any,
  subtitle?: string,
  infoText?: string,
  infoExpanded?: boolean,
  showConfirmButton?: boolean,
  showCloseButton?: boolean,
  showAnimatedDots?: boolean,
  centerContent?: boolean
}

@Component({
  selector: 'app-simple-dialog',
  templateUrl: './simple-dialog.component.html',
  styleUrls: ['./simple-dialog.component.scss']
})
export class SimpleDialogComponent implements AfterViewInit {
  @Output() confirmed = new EventEmitter<boolean>();
  isLoading$ = new BehaviorSubject<boolean>(false);
  initReady = false;

  constructor(public dialogRef: MatDialogRef<SimpleDialogComponent>,
              @Inject(MAT_DIALOG_DATA) public data: DialogData) {
    data.context = data.context || {};
  }

  public static show(message: string, dialog: MatDialog,
                     options?: { loading?: boolean, showConfirmButton?: boolean, showCloseButton?: boolean,
                       disableClose?: boolean, width?: string, showAnimatedDots?: boolean, title?: string,
                       centerContent?: boolean, icon?: string }
  ): MatDialogRef<SimpleDialogComponent> {
    const dialogRef = dialog.open(SimpleDialogComponent, {
      autoFocus: true,
      panelClass: 'absolute',
      width: options?.width || '300px',
      disableClose: (options?.disableClose != undefined)? options?.disableClose: true,
      data: {
        title: options?.title,
        message: message,
        showConfirmButton: options?.showConfirmButton,
        showCloseButton: options?.showCloseButton,
        showAnimatedDots: options?.showAnimatedDots,
        centerContent: options?.centerContent
      }
    });
    if (options?.loading)
      dialogRef.componentInstance.isLoading$.next(true);
    return dialogRef;
  }

  ngAfterViewInit() {
    // workaround for disabling closing-animation of help panel in dialog
    setTimeout(() => this.initReady = true);
  }
}

export function showAPIError(error: any, dialog: MatDialog) {
  const title = `Fehler ${error.status || ''}`;
  let message = '';
  if (error.status === 0)
    message = 'Server antwortet nicht';
  else if (error.error) {
    // usually the backend responds with a message (wrapped in error attribute)
    if (error.error.message)
      // style injection via innerHTML is not trusted, using class to color it red instead
      message = `<span class="red">${error.error.message}</span>`
    else if (typeof(error.error) === 'string'){
      message = error.error;
    }
    else {
      // Rest API responds to malformed requests with a list of fields and the corresponding error
      Object.keys(error.error).forEach(key => {
        message += `<p><b>${key.toUpperCase()}</b>: <span class="red">${error.error[key]}</span></p>`;
      })
    }
  }
  // fallback default message (in most cases very cryptic and not localized)
  else
    message = `<span class="red">${error.message}</span>`

  SimpleDialogComponent.show(message, dialog, {
    title: title, showConfirmButton: true, disableClose: true,
    centerContent: true
  })
}
