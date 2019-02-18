Rails.application.routes.draw do
  devise_for :users, controllers: { registrations: 'registrations' }
  resources :postings
  get '/about', to: 'pages#about'
  root 'pages#index'
end
