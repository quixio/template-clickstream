import { Injectable } from '@angular/core';
import { Observable, BehaviorSubject } from 'rxjs';
import { BaseWssService } from './wss-base.service';
import { EnvironmentVariableService } from './environment-variable.service';

@Injectable({
  providedIn: 'root'
})
export class WssReceiveService extends BaseWssService {
  private messages$: BehaviorSubject<any>;

  constructor(private environmentVariables: EnvironmentVariableService) {
    super();
    this.messages$ = new BehaviorSubject<any>(null);
  }

  public connectAndReceiveMessages(topic: string): Observable<any> {
    var baseUrl = this.environmentVariables.buildUrl('web-socket-subscriber');
    var url = `${baseUrl}/topic/${topic}`;

    this.connect(url);

    this.webSocketSubject.subscribe(
      message => this.messages$.next(message),
      error => {
        if (!this.webSocketSubject.closed) {
          this.webSocketSubject.error(error);
        }
      },
      () => console.log('WebSocket connection completed')
    );

    return this.messages$.asObservable();
  }
  
}