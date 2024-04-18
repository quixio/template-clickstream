import { Component, OnDestroy, OnInit } from '@angular/core';
import { environment } from 'src/environments/environment';
import { User } from './models/user';
import { DataService } from './services/data.service';
import { EnvironmentVariableService } from './services/environment-variable.service';
import { MediaObserver } from '@angular/flex-layout';
import { FormControl } from '@angular/forms';
import { Offer } from './models/offer';
import { actionWords, adjectives, nouns } from './constants/words';
import { CookieService } from 'ngx-cookie-service';
import { WssReceiveService } from './services/wss-receive.service';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit, OnDestroy {

  ages = Array.from({ length: 48 }, (_, i) => i + 18);
  ageControl = new FormControl(this.ages[0]);

  genders = ["Female", "Male", "Unknown"]
  genderControl = new FormControl(this.genders[0]);

  workspaceId: string;
  eventDetectionDeploymentId: string;
  ungatedToken: string;
  user: User;


  constructor(private environmentVariables: EnvironmentVariableService,
    private dataService: DataService,
    public media: MediaObserver,
    private cookieService: CookieService,
    private wssReceiveService: WssReceiveService) { }

  ngOnDestroy(): void {
    this.wssReceiveService.disconnect();
  }

  ngOnInit(): void {
    const userId = this.cookieService.get('userId') || this.generateUniqueWords();
    this.cookieService.set('userId', userId);
    this.generateUniqueWords();
    this.user = {
      userId: userId,
      gender: this.genderControl.value || "Female",
      age: this.ageControl.value || 18
    };

    this.ungatedToken = this.environmentVariables.ungatedToken;
    this.eventDetectionDeploymentId = environment.EVT_DETECT_DEPLOYMENT_ID || '';

    this.ageControl.valueChanges.subscribe((age) => {
      this.user.age = age || 0;
      this.dataService.user.age = this.user.age;
    });

    this.genderControl.valueChanges.subscribe((gender) => {
      this.user.gender = gender || "Unknown";
      this.dataService.user.gender = this.user.gender;
    });

    this.dataService.user = this.user;

    this.environmentVariables.offersTopic$.subscribe(topic => {
      if (topic) {
        this.wssReceiveService.connectAndReceiveMessages(topic).subscribe(
          message => {
            console.log(message)
            if (message == null) return;
            const offer = new Offer(JSON.parse(message));
            if (offer.IsValid && offer.Offer !== undefined && !this.dataService.isDialogOpen){
              this.dataService.openDialog(offer)
            }   
          }
        );
      }
    });
  }

  toggleSidenav(isOpen: boolean): void {
    this.dataService.isSidenavOpen$.next(isOpen);
  }

  generateUniqueWords(): string {
    const uniqueWords: string[] = [];

    while (uniqueWords.length < 3) {
      let randomWord: string;

      if (uniqueWords.length === 0) {
        const randomIndex = Math.floor(Math.random() * adjectives.length);
        randomWord = adjectives[randomIndex];
      } else if (uniqueWords.length === 1) {
        const randomIndex = Math.floor(Math.random() * nouns.length);
        randomWord = nouns[randomIndex];
      } else {
        const randomIndex = Math.floor(Math.random() * actionWords.length);
        randomWord = actionWords[randomIndex];
      }

      if (!uniqueWords.includes(randomWord)) {
        uniqueWords.push(randomWord);
      }
    }

    return uniqueWords.join('-');
  }
}
