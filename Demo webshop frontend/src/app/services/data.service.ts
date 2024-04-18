import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { Subject, map } from 'rxjs';
import { DialogComponent } from '../components/dialog/dialog.component';
import { User } from '../models/user';
import { Offer } from '../models/offer';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  user: User;
  userIp: string;
  categorySelection: string[];
  isSidenavOpen$ = new Subject<boolean>();
  isDialogOpen = false;
  dialogRef: MatDialogRef<DialogComponent>;

  constructor(private http: HttpClient, private dialog: MatDialog) {}

  getIpAddress(): Observable<string> {
    return this.http.get("https://api.ipify.org/?format=json").pipe(map((m: any) => m.ip));
  }

  openDialog(data: Offer): void {
    this.dialog.open(DialogComponent, {
      width: '70vh',
      data,
      backdropClass: 'bg-transparent'
    });

    this.isDialogOpen = true;
    
    this.dialogRef.afterClosed().subscribe(() => {
      this.isDialogOpen = false;
    });
  }
}
