import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Subject, map } from 'rxjs';
import { DialogComponent } from '../components/dialog/dialog.component';
import { User } from '../models/user';
import { EventData } from '../models/eventData';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class DataService {
  user: User;
  userIp: string;
  categorySelection: string[];
  isSidenavOpen$ = new Subject<boolean>();

  constructor(private http: HttpClient, private dialog: MatDialog) {}

  getIpAddress(): Observable<string> {
    return this.http.get("https://api.ipify.org/?format=json").pipe(map((m: any) => m.ip));
  }

  openDialog(data: EventData): void {
    this.dialog.open(DialogComponent, {
      width: '70vh',
      data,
      backdropClass: 'bg-transparent'
    });
  }
}
